# ai_services/audit_service.py

import json
from typing import Dict, Any
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from .taxonomy import get_ai_taxonomy
from config import get_settings

settings = get_settings()

def get_gemini_client():
    return genai.Client(api_key=settings.google_api_key)

def perform_ai_audit(incident_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Performs a semantic audit of an incident report to detect mismatches
    between the narrative description and the structured metadata fields.
    Returns a dictionary of flagged fields with reasons.
    """
    client = get_gemini_client()
    taxonomy = get_ai_taxonomy(db)
    
    # Construct the Audit Prompt
    prompt = f"""
You are an expert Safety Incident Auditor performing SEMANTIC VALIDATION.
Check if the following incident fields are CONSISTENT with the incident description.

REFERENCE TAXONOMY:
- Hierarchy (Group -> SubGroup): {json.dumps(taxonomy.get("subgroup_rules", {}))}
- Risk Categories: {taxonomy.get("incident_risk_category", [])}
- Operational Activities: {taxonomy.get("operational_activities", [])}
- Areas of Incident: {taxonomy.get("areas", [])}
- Severity Levels: 1-Negligible (First aid), 2-Minor (No lost time), 3-Moderate (Medical treatment), 4-Major (Disability), 5-Catastrophic (Fatality)

INCIDENT DATA TO AUDIT:
{json.dumps(incident_data, indent=2)}

TASK:
Report ONLY fields with CLEAR MISMATCH, LOGICAL CONTRADICTION, or TAXONOMY VIOLATION.
Skip fields that are consistent or undeterminable.

Consider:
1. Does 'actual_severity' match the harm described? (e.g. 'Broken Leg' is NOT 'Negligible')
2. Does 'risk_category' align with the event? (e.g. 'Falling' is NOT 'Fire')
3. Does 'sub_group' belong to the 'incident_group'?
4. Does 'area_of_incident' match the location mentioned?

OUTPUT (JSON only):
Return a JSON object where keys are the field names that have issues.
Example format:
{{
    "actual_severity": {{
        "isValid": false,
        "score": 8,
        "reason": "Description mentions a 'fractured arm' which typically requires medical treatment (Moderate), but severity is set to 'Negligible'."
    }},
    "incident_group": {{
        "isValid": false,
        "score": 7,
        "reason": "The selected group does not align with the 'Slip, Trip & Fall' event described."
    }}
}}

If everything matches perfectly, return an empty object: {{}}
Return ONLY the raw JSON. Do not include markdown fences.
"""

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0,
            ),
        )
        
        # Parse result
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return data

    except Exception as e:
        import traceback
        print(f"❌ ERROR in perform_ai_audit: {str(e)}")
        traceback.print_exc()
        return {"error": str(e), "message": "Failed to perform AI Audit. Please check API key and logs."}
