# ai_services/prompts.py

def get_incident_analysis_prompt(taxonomy: dict, user_context: str = "") -> str:
    """
    Constructs the system prompt for Gemini based on current DB taxonomy and optional user context.
    """
    
    incident_types = ", ".join(taxonomy.get("incident_type", []))
    incident_groups = ", ".join(taxonomy.get("incident_group", []))
    risk_categories = ", ".join(taxonomy.get("risk_category", []))
    severities = ", ".join(taxonomy.get("severity_level", []))
    activities = ", ".join(taxonomy.get("operational_activities", []))
    
    # Subgroup rules
    rules_text = ""
    for group, subgroups in taxonomy.get("subgroup_rules", {}).items():
        rules_text += f"- {group}: {', '.join(subgroups)}\n"

    # User provided context
    context_section = ""
    if user_context:
        context_section = f"\nUSER PROVIDED CONTEXT / DESCRIPTION:\n{user_context}\n"

    prompt = f"""
Analyze the provided media (image, video, or audio) and optional user description, then return a SINGLE JSON object representing a formal safety incident report.
ALL fields are REQUIRED and MUST be non-empty. Use the user provided context to improve accuracy.
{context_section}
JSON Structure:
{{
  "incident_title": "Short, clear title (e.g., 'Forklift Collision near Warehouse A')",
  "incident_type": ["One value from ALLOWED TYPES"],
  "incident_group": ["One value from ALLOWED GROUPS"],
  "sub_group": ["One valid subgroup for the selected group"],
  "operational_activity": "One value from ALLOWED ACTIVITIES",
  "risk_category": "One value from ALLOWED RISKS",
  "area_of_incident": "One value from ALLOWED AREAS",
  "actual_severity": "One value from ALLOWED SEVERITIES",
  "potential_severity": "One value from ALLOWED SEVERITIES",
  "critical_incident": "Yes or No",
  "description": "Two paragraphs separated by \\n\\n: detailed factual account of the event and its immediate impact. Use provided context if available.",
  "immediate_action": "A bulleted list using '-':\\n- Immediate action: ...\\n- Corrective action: ...\\n- Preventive action: ..."
}}

ALLOWED TYPES: {incident_types}
ALLOWED GROUPS: {incident_groups}
ALLOWED ACTIVITIES: {activities}
ALLOWED RISKS: {risk_categories}
ALLOWED AREAS: {taxonomy.get("areas", [])}
ALLOWED SEVERITIES: {severities} (1-Negligible, 2-Minor, etc.)

HIERARCHY RULES (Group -> Subgroups):
{rules_text}

Rules for selection:
1. First, select the most appropriate Group.
2. Then, pick a valid Subgroup for that group from the hierarchy rules.
3. If the event is severe (e.g., Catastrophic or Major), set critical_incident to 'Yes'.
4. BOTH description and immediate_action MUST be PLAIN TEXT without any HTML tags (<p>, <ul>, <li>, etc.).
5. Use standard line breaks (\\n) for spacing.
6. incident_type, incident_group, and sub_group MUST be lists containing exactly one string.

Do not include any markers like ```json or markdown fences. Return ONLY the raw JSON string.
"""
    return prompt.strip()
