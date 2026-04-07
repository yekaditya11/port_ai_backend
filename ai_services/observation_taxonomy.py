from sqlalchemy.orm import Session

from models.enums import ObservationEnumValue, ObservationReviewFactor
from models.reference import SubArea


def _group_enum_values(rows):
    taxonomy = {}
    for row in rows:
        taxonomy.setdefault(row.category, []).append(row.value)
    return taxonomy


def _build_parent_mapping(rows):
    mapping = {}
    for row in rows:
        if row.parent_value:
            mapping.setdefault(row.parent_value, []).append(row.value)
    return mapping


def _get_sub_area_mapping(db: Session):
    mapping = {}
    rows = db.query(SubArea.area_name, SubArea.sub_area_name).all()
    for area_name, sub_area_name in rows:
        if area_name and sub_area_name:
            mapping.setdefault(area_name, []).append(sub_area_name)
    return mapping


def get_observation_ai_taxonomy(db: Session):
    """
    Fetches observation-specific dropdown values from observation_enums.
    Returns a dict with categories as keys and lists of strings as values.
    """
    enums = (
        db.query(ObservationEnumValue)
        .order_by(
            ObservationEnumValue.category,
            ObservationEnumValue.sort_order,
            ObservationEnumValue.id,
        )
        .all()
    )
    taxonomy = _group_enum_values(enums)
    taxonomy["specific_detail_rules"] = _build_parent_mapping(
        [e for e in enums if e.category == "observation_specific_detail"]
    )
    taxonomy["sub_area_rules"] = _get_sub_area_mapping(db)
    return taxonomy


def get_observation_review_factor_taxonomy(db: Session):
    """
    Fetches primary factors with their allowed preconditions and underlying causes.
    The LLM needs this hierarchy so child options match the selected primary factor.
    """
    rows = (
        db.query(ObservationReviewFactor)
        .order_by(
            ObservationReviewFactor.type,
            ObservationReviewFactor.parent_id,
            ObservationReviewFactor.sort_order,
            ObservationReviewFactor.id,
        )
        .all()
    )

    primary_factors = [
        {"id": row.id, "label": row.value}
        for row in rows
        if row.type == "primary_factor"
    ]
    preconditions_by_primary = {}
    causes_by_primary = {}

    for row in rows:
        if row.type == "precondition" and row.parent_id:
            preconditions_by_primary.setdefault(row.parent_id, []).append(
                {"id": row.id, "label": row.value}
            )
        elif row.type == "underlying_cause" and row.parent_id:
            causes_by_primary.setdefault(row.parent_id, []).append(
                {"id": row.id, "label": row.value}
            )

    return {
        "primary_factors": primary_factors,
        "preconditions_by_primary": preconditions_by_primary,
        "underlying_causes_by_primary": causes_by_primary,
    }
