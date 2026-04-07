import json


def _format_options(values: list[str]) -> str:
    return ", ".join(values) if values else "None available"


def _format_rules(mapping: dict[str, list[str]]) -> str:
    if not mapping:
        return "- None available"

    lines = []
    for parent, children in mapping.items():
        lines.append(f"- {parent}: {', '.join(children)}")
    return "\n".join(lines)


def _format_context_section(user_context: str) -> str:
    if not user_context:
        return ""
    return f"\nUSER PROVIDED CONTEXT / DESCRIPTION:\n{user_context}\n"


def get_observation_analysis_prompt(taxonomy: dict, user_context: str = "") -> str:
    """
    Constructs the observation prompt for Gemini based on observation_enums and optional user context.
    """
    prompt = f"""
Analyze the provided media (image or video) and optional user description, then return a SINGLE JSON object for prefilling an observation form.
Choose enum-backed fields only from the allowed options. Use the user provided context to improve accuracy.
{_format_context_section(user_context)}
JSON Structure:
{{
  "area_of_observation": "One value from ALLOWED AREAS",
  "business_unit": "One value from ALLOWED BUSINESS UNITS",
  "department": "One value from ALLOWED DEPARTMENTS",
  "designation": "One value from ALLOWED DESIGNATIONS",
  "operational_activity": "One value from ALLOWED OPERATIONAL ACTIVITIES",
  "observation_group": "One value from ALLOWED OBSERVATION GROUPS",
  "specific_detail": "Short, specific plain-text detail describing the unsafe act, unsafe condition, or noteworthy event",
  "description": "Two paragraphs separated by \\n\\n: a clear factual observation summary and the likely consequence or risk. Use provided context if available.",
  "near_miss": true,
  "time_of_day": "One value from ALLOWED TIMES OF DAY or null",
  "shift": "One value from ALLOWED SHIFTS or null",
  "operational_department": "One value from ALLOWED OPERATIONAL DEPARTMENTS",
  "sub_area": null,
  "weather": "One value from ALLOWED WEATHER or null",
  "observation_type": "One value from ALLOWED OBSERVATION TYPES or null",
  "potential_severity": "One value from ALLOWED SEVERITIES or null",
  "observation_category": "One value from ALLOWED OBSERVATION CATEGORIES or null",
  "hazard_category": "One value from ALLOWED HAZARD CATEGORIES or null",
  "risk_category": "One value from ALLOWED RISK CATEGORIES or null",
  "immediate_action": "A bulleted list using '-':\\n- Immediate action: ...\\n- Corrective action: ...\\n- Preventive action: ..."
}}

ALLOWED AREAS: {_format_options(taxonomy.get("area_of_observation", []))}
ALLOWED BUSINESS UNITS: {_format_options(taxonomy.get("business_unit", []))}
ALLOWED DEPARTMENTS: {_format_options(taxonomy.get("department", []))}
ALLOWED DESIGNATIONS: {_format_options(taxonomy.get("designation", []))}
ALLOWED OPERATIONAL DEPARTMENTS: {_format_options(taxonomy.get("operational_department", []))}
ALLOWED OPERATIONAL ACTIVITIES: {_format_options(taxonomy.get("operational_activity", []))}
ALLOWED TIMES OF DAY: {_format_options(taxonomy.get("time_of_day", []))}
ALLOWED SHIFTS: {_format_options(taxonomy.get("shift", []))}
ALLOWED WEATHER: {_format_options(taxonomy.get("weather", []))}
ALLOWED OBSERVATION TYPES: {_format_options(taxonomy.get("observation_type", []))}
ALLOWED SEVERITIES: {_format_options(taxonomy.get("severity_level", []))}
ALLOWED OBSERVATION CATEGORIES: {_format_options(taxonomy.get("observation_category", []))}
ALLOWED HAZARD CATEGORIES: {_format_options(taxonomy.get("hazard_category", []))}
ALLOWED OBSERVATION GROUPS: {_format_options(taxonomy.get("observation_group", []))}
ALLOWED RISK CATEGORIES: {_format_options(taxonomy.get("risk_category", []))}
ALLOWED SUB-AREA RULES: {_format_rules(taxonomy.get("sub_area_rules", {}))}

Rules for selection:
1. Use BEST GUESS for business_unit, department, designation, and operational_department when the media or context is ambiguous.
2. specific_detail, description, and immediate_action MUST be PLAIN TEXT without any HTML tags.
3. near_miss MUST be a boolean true or false value.
4. Do NOT return reported_date, reported_time, or reporter_confirmation.
5. Set sub_area to null if the media/context is insufficient or if there is no reliable matching sub-area option.
6. Return null for optional fields when they cannot be inferred confidently.
7. Do not include any keys other than the ones shown in the JSON Structure.

Do not include any markers like ```json or markdown fences. Return ONLY the raw JSON string.
"""
    return prompt.strip()


def _format_review_factor_hierarchy(taxonomy: dict) -> str:
    lines = []
    preconditions_by_primary = taxonomy.get("preconditions_by_primary", {})
    causes_by_primary = taxonomy.get("underlying_causes_by_primary", {})

    for primary in taxonomy.get("primary_factors", []):
        primary_id = primary["id"]
        lines.append(f"- Primary factor {primary_id}: {primary['label']}")
        lines.append(
            f"  Preconditions: {json.dumps(preconditions_by_primary.get(primary_id, []), ensure_ascii=False)}"
        )
        lines.append(
            f"  Underlying causes: {json.dumps(causes_by_primary.get(primary_id, []), ensure_ascii=False)}"
        )

    return "\n".join(lines) if lines else "- None available"


def get_observation_review_analysis_prompt(
    observation_data: dict,
    factor_taxonomy: dict,
) -> str:
    """
    Constructs the prompt for AI-assisted observation review prefill.
    """
    prompt = f"""
You are a port safety reviewer. Review the observation record and return a SINGLE JSON object that can prefill an observation review form.

OBSERVATION RECORD:
{json.dumps(observation_data, indent=2, default=str, ensure_ascii=False)}

AVAILABLE UNSAFE ABC FACTORS:
{_format_review_factor_hierarchy(factor_taxonomy)}

JSON Structure:
{{
  "review_mode": "NEAR_MISS",
  "review_comments": "A concise reviewer comment generated from the observation record.",
  "next_action": "Action",
  "unsafe_abc": [
    {{
      "primaryFactor": "1",
      "precondition": "4",
      "underlyingCause": "7",
      "cause": "A concise cause explanation generated from the observation record."
    }}
  ]
}}

Rules:
1. review_mode MUST be exactly one of: "NEAR_MISS", "INCIDENT".
2. next_action MUST be exactly one of: "Action", "Close", "Reject".
3. Choose primaryFactor from AVAILABLE UNSAFE ABC FACTORS primary factor IDs only.
4. After choosing primaryFactor, choose precondition only from that primary factor's Preconditions list.
5. After choosing primaryFactor, choose underlyingCause only from that primary factor's Underlying causes list.
6. primaryFactor, precondition, and underlyingCause MUST be returned as strings containing the selected numeric ID.
7. unsafe_abc MUST contain exactly one object.
8. review_comments and cause MUST be plain text without HTML or markdown.
9. Prefer next_action "Action" when a corrective/preventive action is needed, "Close" when no further action is required, and "Reject" only when the observation is invalid or not safety-related.
10. Do not include any keys other than the ones shown in the JSON Structure.

Do not include any markers like ```json or markdown fences. Return ONLY the raw JSON string.
"""
    return prompt.strip()
