import json
import os
import tempfile
import time
from typing import Callable, List, Tuple

from sqlalchemy.orm import Session

from .observation_prompts import (
    get_observation_analysis_prompt,
    get_observation_review_analysis_prompt,
)
from .observation_taxonomy import (
    get_observation_ai_taxonomy,
    get_observation_review_factor_taxonomy,
)
from config import get_settings

settings = get_settings()

genai = None
types = None

OBSERVATION_AI_FAILURE_MESSAGE = "Failed to analyze observation media with AI."
REVIEW_AI_FAILURE_MESSAGE = "Failed to generate observation review with AI."
OBSERVATION_ANALYSIS_FIELDS = (
    "area_of_observation",
    "business_unit",
    "department",
    "designation",
    "operational_activity",
    "observation_group",
    "specific_detail",
    "description",
    "near_miss",
    "time_of_day",
    "shift",
    "operational_department",
    "sub_area",
    "weather",
    "observation_type",
    "potential_severity",
    "observation_category",
    "hazard_category",
    "risk_category",
    "immediate_action",
)
REVIEW_MODES = {"NEAR_MISS", "INCIDENT"}
NEXT_ACTIONS = {"Action", "Close", "Reject"}


def get_observation_gemini_client():
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


def _normalize_text(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _normalize_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "y", "1"}:
            return True
        if normalized in {"false", "no", "n", "0"}:
            return False
    return default


def _build_observation_gemini_parts(client, media_data: List[Tuple[bytes, str]]):
    parts = []
    temp_files_on_disk = []
    gemini_files_to_delete = []

    for file_bytes, content_type in media_data:
        content_type_lower = (content_type or "").lower()
        is_image = "image" in content_type_lower
        is_video = "video" in content_type_lower
        is_audio = "audio" in content_type_lower

        if is_image:
            parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=content_type or "application/octet-stream",
                )
            )
        elif is_video or is_audio:
            suffix = ".mp4" if is_video else ".mp3"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
                temp_files_on_disk.append(tmp_path)

            file_metadata = client.files.upload(file=tmp_path)

            while file_metadata.state.name == "PROCESSING":
                time.sleep(2)
                file_metadata = client.files.get(name=file_metadata.name)

            if file_metadata.state.name == "FAILED":
                continue

            parts.append(file_metadata)
            gemini_files_to_delete.append(file_metadata.name)

    return parts, temp_files_on_disk, gemini_files_to_delete


def _cleanup_observation_gemini_files(client, temp_files_on_disk, gemini_files_to_delete):
    for name in gemini_files_to_delete:
        try:
            client.files.delete(name=name)
        except Exception:
            pass

    for path in temp_files_on_disk:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _post_process_observation_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Gemini did not return a JSON object.")

    cleaned = {}
    for field in OBSERVATION_ANALYSIS_FIELDS:
        value = data.get(field)
        if field == "near_miss":
            cleaned[field] = _normalize_bool(value)
        else:
            cleaned[field] = _normalize_text(value)

    cleaned["sub_area"] = cleaned.get("sub_area") or None
    return cleaned


def _normalize_review_mode(value) -> str:
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in REVIEW_MODES:
            return normalized
    return "INCIDENT"


def _normalize_next_action(value) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        for action in NEXT_ACTIONS:
            if normalized == action.lower():
                return action
    return "Action"


def _normalize_factor_id(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, int):
        return str(value)
    return str(value)


def _valid_factor_child_ids(factor_taxonomy: dict, key: str, primary_factor_id):
    if not primary_factor_id:
        return set()

    try:
        parent_id = int(primary_factor_id)
    except (TypeError, ValueError):
        return set()

    return {
        str(item["id"])
        for item in factor_taxonomy.get(key, {}).get(parent_id, [])
    }


def _post_process_observation_review_payload(data: dict, factor_taxonomy: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Gemini did not return a JSON object.")

    unsafe_abc = data.get("unsafe_abc")
    unsafe_abc_item = unsafe_abc[0] if isinstance(unsafe_abc, list) and unsafe_abc else {}
    if not isinstance(unsafe_abc_item, dict):
        unsafe_abc_item = {}

    primary_factor = _normalize_factor_id(unsafe_abc_item.get("primaryFactor"))
    valid_primary_ids = {
        str(item["id"]) for item in factor_taxonomy.get("primary_factors", [])
    }
    if primary_factor not in valid_primary_ids:
        primary_factor = None

    precondition = _normalize_factor_id(unsafe_abc_item.get("precondition"))
    valid_precondition_ids = _valid_factor_child_ids(
        factor_taxonomy,
        "preconditions_by_primary",
        primary_factor,
    )
    if precondition not in valid_precondition_ids:
        precondition = None

    underlying_cause = _normalize_factor_id(unsafe_abc_item.get("underlyingCause"))
    valid_cause_ids = _valid_factor_child_ids(
        factor_taxonomy,
        "underlying_causes_by_primary",
        primary_factor,
    )
    if underlying_cause not in valid_cause_ids:
        underlying_cause = None

    return {
        "review_mode": _normalize_review_mode(data.get("review_mode")),
        "review_comments": _normalize_text(data.get("review_comments")),
        "next_action": _normalize_next_action(data.get("next_action")),
        "unsafe_abc": [
            {
                "primaryFactor": primary_factor,
                "precondition": precondition,
                "underlyingCause": underlying_cause,
                "cause": _normalize_text(unsafe_abc_item.get("cause")),
            }
        ],
    }


def _run_observation_media_prompt(
    media_data: List[Tuple[bytes, str]],
    prompt: str,
    post_process: Callable[[dict], dict],
) -> dict:
    client = None
    temp_files_on_disk = []
    gemini_files_to_delete = []

    try:
        client = get_observation_gemini_client()
        parts, temp_files_on_disk, gemini_files_to_delete = _build_observation_gemini_parts(
            client,
            media_data,
        )

        if not parts:
            raise ValueError("No valid media files were successfully processed.")

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=parts + [prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return post_process(data)

    except Exception as e:
        print(f"ERROR in analyze_observation_media: {str(e)}")
        return {"error": str(e), "message": OBSERVATION_AI_FAILURE_MESSAGE}

    finally:
        if client is not None:
            _cleanup_observation_gemini_files(
                client,
                temp_files_on_disk,
                gemini_files_to_delete,
            )


def _run_observation_text_json_prompt(
    prompt: str,
    post_process: Callable[[dict], dict],
    failure_message: str,
) -> dict:
    try:
        client = get_observation_gemini_client()
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return post_process(data)

    except Exception as e:
        print(f"ERROR in observation_review_ai: {str(e)}")
        return {"error": str(e), "message": failure_message}


def analyze_observation_media(
    media_data: List[Tuple[bytes, str]],
    db: Session,
    user_context: str = "",
) -> dict:
    """
    Analyzes observation media using observation_enums to prefill the observation form.
    """
    taxonomy = get_observation_ai_taxonomy(db)
    prompt = get_observation_analysis_prompt(taxonomy, user_context)
    return _run_observation_media_prompt(
        media_data,
        prompt,
        _post_process_observation_payload,
    )


def analyze_observation_review(observation_data: dict, db: Session) -> dict:
    """
    Uses Gemini to suggest review fields for an existing observation record.
    """
    factor_taxonomy = get_observation_review_factor_taxonomy(db)
    prompt = get_observation_review_analysis_prompt(observation_data, factor_taxonomy)
    return _run_observation_text_json_prompt(
        prompt,
        lambda data: _post_process_observation_review_payload(data, factor_taxonomy),
        REVIEW_AI_FAILURE_MESSAGE,
    )
