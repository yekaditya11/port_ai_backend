import json
from datetime import datetime

from config import get_settings

settings = get_settings()

genai = None
types = None

QUERY_CATALOG = [
    {
        "id": "incident_count",
        "intent": "incident",
        "description": "Count incidents for a date range or all time.",
    },
    {
        "id": "observation_count",
        "intent": "observation",
        "description": "Count observations for a date range or all time.",
    },
    {
        "id": "safety_event_count",
        "intent": "both",
        "description": "Count incidents and observations together for a date range or all time.",
    },
    {
        "id": "latest_incidents",
        "intent": "incident",
        "description": "Show latest incidents.",
    },
    {
        "id": "latest_observations",
        "intent": "observation",
        "description": "Show latest observations.",
    },
    {
        "id": "latest_safety_events",
        "intent": "both",
        "description": "Show latest incidents and observations together.",
    },
    {
        "id": "incident_by_status",
        "intent": "incident",
        "description": "Group incidents by status.",
    },
    {
        "id": "observation_by_status",
        "intent": "observation",
        "description": "Group observations by status.",
    },
    {
        "id": "incident_by_area",
        "intent": "incident",
        "description": "Group incidents by area_of_incident.",
    },
    {
        "id": "observation_by_area",
        "intent": "observation",
        "description": "Group observations by area_of_observation.",
    },
    {
        "id": "incident_by_activity",
        "intent": "incident",
        "description": "Group incidents by operational_activity.",
    },
    {
        "id": "observation_by_activity",
        "intent": "observation",
        "description": "Group observations by operational_activity.",
    },
    {
        "id": "observation_near_miss_count",
        "intent": "observation",
        "description": "Count near miss observations.",
    },
    {
        "id": "incident_detail",
        "intent": "incident",
        "description": "Get one incident by incident_ref.",
        "required_param": "reference",
    },
    {
        "id": "observation_detail",
        "intent": "observation",
        "description": "Get one observation by observation_ref.",
        "required_param": "reference",
    },
]

def get_chatbot_gemini_client():
    global genai, types

    if genai is None or types is None:
        try:
            from google import genai as google_genai
            from google.genai import types as google_genai_types
        except ImportError as exc:
            raise RuntimeError(
                "Gemini SDK is not installed. Install `google-genai` in this virtual environment."
            ) from exc

        genai = google_genai
        types = google_genai_types

    return genai.Client(api_key=settings.google_api_key)


def build_chatbot_planner_prompt(message: str) -> str:
    current_datetime = datetime.now()
    return f"""
You are a query planner for a port safety chatbot. Choose exactly one query template from the catalog.

CURRENT DATE: {current_datetime.date().isoformat()}
CURRENT TIME: {current_datetime.time().replace(microsecond=0).isoformat()}
CURRENT DATETIME: {current_datetime.replace(microsecond=0).isoformat()}

QUERY CATALOG:
{json.dumps(QUERY_CATALOG, indent=2)}

Allowed date_range values:
- "today"
- "yesterday"
- "last_7_days"
- "last_30_days"
- "this_month"
- "all"
- "custom"

Rules:
1. Return only raw JSON. No markdown.
2. query_id must be one of the catalog IDs.
3. intent must be "incident", "observation", "both", or "unknown".
4. response_type must be "text", "table", or "both".
5. If the user asks for a list, details, latest records, grouping, or comparison, prefer response_type "both".
6. If the user asks "how many", prefer response_type "text".
7. Use limit between 1 and 50. Default limit is 10.
8. If a reference like INC00000001 or OBS963235321 is present, put it in params.reference.
9. For custom date ranges, set params.from_date and params.to_date as YYYY-MM-DD.
10. If no template fits, set query_id to "unknown".

Expected JSON:
{{
  "intent": "observation",
  "query_id": "latest_observations",
  "response_type": "both",
  "params": {{
    "date_range": "all",
    "from_date": null,
    "to_date": null,
    "limit": 10,
    "reference": null
  }}
}}

USER MESSAGE:
{message}
""".strip()


def _clean_json_response(text: str) -> dict:
    raw_text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw_text)


def plan_chatbot_query(message: str) -> dict:
    client = get_chatbot_gemini_client()
    prompt = build_chatbot_planner_prompt(message)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    data = _clean_json_response(response.text or "{}")

    if not isinstance(data, dict):
        raise ValueError("Gemini did not return a JSON object.")

    catalog_ids = {item["id"] for item in QUERY_CATALOG}
    query_id = data.get("query_id")
    if query_id not in catalog_ids:
        query_id = "unknown"

    params = data.get("params")
    if not isinstance(params, dict):
        params = {}

    response_type = data.get("response_type")
    if response_type not in {"text", "table", "both"}:
        response_type = "text"

    intent = data.get("intent")
    if intent not in {"incident", "observation", "both", "unknown"}:
        intent = "unknown"

    limit = params.get("limit", 10)
    try:
        limit = max(1, min(int(limit), 50))
    except (TypeError, ValueError):
        limit = 10

    return {
        "intent": intent,
        "query_id": query_id,
        "response_type": response_type,
        "params": {
            "date_range": params.get("date_range") or "all",
            "from_date": params.get("from_date"),
            "to_date": params.get("to_date"),
            "limit": limit,
            "reference": params.get("reference"),
        },
    }


def build_chatbot_formatter_prompt(
    message: str,
    plan: dict,
    query_result: dict,
) -> str:
    current_datetime = datetime.now()
    return f"""
You are the final response formatter for a port safety chatbot.
You receive the user's message, the selected query plan, and the safe SQL result.
Decide whether the final response should be text only, table only, or both.

CURRENT DATE: {current_datetime.date().isoformat()}
CURRENT TIME: {current_datetime.time().replace(microsecond=0).isoformat()}
CURRENT DATETIME: {current_datetime.replace(microsecond=0).isoformat()}

Rules:
1. Return only raw JSON. No markdown.
2. response_type must be exactly "text", "table", or "both".
3. Use "text" when the result is a single number or a short direct answer.
4. Use "table" when the user mainly asked to list records and no extra explanation is needed.
5. Use "both" when the user asked for a summary, comparison, trends, grouped counts, details, or when a table benefits from explanation.
6. answer must be a concise natural-language response based only on SQL_RESULT.
7. Do not invent records, counts, dates, or fields.
8. If SQL_RESULT.table is empty, explain that no matching records were found and choose "text".
9. Do not include the table rows in your JSON. The backend will attach the table when response_type is "table" or "both".
10. For query_id "incident_detail" or "observation_detail", explain the event in simple terms for a non-technical user.
11. For detail queries, include what happened, current status, where it happened, when it happened, and any immediate action if those fields are present.
12. For detail queries, prefer response_type "both" when a matching record exists so the frontend can show the simple explanation plus the source row.
13. For query_id "observation_near_miss_count", if preview rows are present, prefer response_type "both"; answer should mention the total count and that the table shows the latest preview records.

Expected JSON:
{{
  "answer": "There are 6 observations in total.",
  "response_type": "text"
}}

USER MESSAGE:
{message}

QUERY PLAN:
{json.dumps(plan, indent=2, default=str)}

SQL_RESULT:
{json.dumps(query_result, indent=2, default=str)}
""".strip()


def format_chatbot_response(
    message: str,
    plan: dict,
    query_result: dict,
) -> dict:
    client = get_chatbot_gemini_client()
    prompt = build_chatbot_formatter_prompt(message, plan, query_result)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    data = _clean_json_response(response.text or "{}")

    if not isinstance(data, dict):
        raise ValueError("Gemini did not return a JSON object.")

    answer = data.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        answer = query_result.get("answer") or "I found the requested result."

    response_type = data.get("response_type")
    if response_type not in {"text", "table", "both"}:
        response_type = plan.get("response_type")
    if response_type not in {"text", "table", "both"}:
        response_type = "text"

    table = query_result.get("table")
    if not table or not table.get("rows"):
        response_type = "text"
    elif plan.get("query_id") == "observation_near_miss_count":
        response_type = "both"
    elif response_type == "text":
        table = None

    return {
        "answer": answer.strip(),
        "response_type": response_type,
        "table": table if response_type in {"table", "both"} else None,
    }
