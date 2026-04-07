from typing import List

from datetime import date, datetime, time, timedelta
from secrets import randbelow

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models.enums import ObservationReviewFactor
from models.observation import Observation, ObservationReview
from schemas.schemas import (
    ObservationCreate,
    ObservationFactorOption,
    ObservationFactorOptionsResponse,
    ObservationListItem,
    ObservationListResponse,
    ObservationReviewCreate,
    ObservationReviewResponse,
    ObservationSummaryStats,
    ObservationStatsBucket,
    ObservationStatsResponse,
    ObservationTimelinePoint,
    ObservationResponse,
)

router = APIRouter(tags=["Observations"])

OBSERVATION_REF_ATTEMPTS = 20

try:
    import multipart  # noqa: F401
    MULTIPART_INSTALLED = True
except ImportError:
    MULTIPART_INSTALLED = False


def generate_observation_ref(db: Session) -> str:
    for _ in range(OBSERVATION_REF_ATTEMPTS):
        observation_ref = f"OBS{randbelow(1_000_000_000):09d}"
        exists = (
            db.query(Observation.id)
            .filter(Observation.observation_ref == observation_ref)
            .first()
        )
        if not exists:
            return observation_ref

    raise HTTPException(status_code=500, detail="Unable to generate unique observation reference")


if MULTIPART_INSTALLED:
    @router.post("/api/observations/analyze/")
    async def analyze_observation(
        files: List[UploadFile] = File(...),
        description: str = Form(None),
        db: Session = Depends(get_db),
    ):
        """Analyze multiple uploaded images/videos with Gemini AI for observation form population."""
        from ai_services.observation_gemini_service import analyze_observation_media

        media_data = []
        for file in files:
            file_bytes = await file.read()
            media_data.append((file_bytes, file.content_type))

        return analyze_observation_media(media_data, db, user_context=description or "")
else:
    @router.post("/api/observations/analyze/")
    async def analyze_observation_unavailable():
        raise HTTPException(
            status_code=503,
            detail="AI analysis is unavailable. Install `python-multipart` and `google-genai` in the active virtual environment.",
        )


def apply_observation_date_filters(query, from_date: date | None, to_date: date | None):
    if from_date:
        query = query.filter(Observation.reported_date >= datetime.combine(from_date, time.min))
    if to_date:
        query = query.filter(Observation.reported_date <= datetime.combine(to_date, time.max))
    return query


def grouped_observation_counts(
    db: Session,
    column,
    from_date: date | None = None,
    to_date: date | None = None,
):
    query = (
        db.query(column.label("name"), func.count(Observation.id).label("value"))
        .filter(column.is_not(None), column != "")
    )
    query = apply_observation_date_filters(query, from_date, to_date)

    rows = (
        query.group_by(column)
        .order_by(desc("value"), column.asc())
        .all()
    )

    return [ObservationStatsBucket(name=row.name, value=row.value) for row in rows]


def filtered_observation_query(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
):
    return apply_observation_date_filters(db.query(Observation), from_date, to_date)


def observation_to_ai_payload(observation: Observation) -> dict:
    data = {}
    for column in Observation.__table__.columns:
        value = getattr(observation, column.name)
        if isinstance(value, (datetime, date, time)):
            value = value.isoformat()
        data[column.name] = value
    return data


@router.get("/api/observations/stats/", response_model=ObservationStatsResponse)
def observation_stats(
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    base_query = filtered_observation_query(db, from_date, to_date)

    near_misses = base_query.filter(Observation.near_miss.is_(True)).count()
    overdue = base_query.filter(func.lower(Observation.status) == "overdue").count()
    closed_on_time = base_query.filter(
        func.lower(Observation.status).in_(
            ["closed", "closed on time", "resolved", "resolution", "completed"]
        )
    ).count()
    last_24h = base_query.filter(Observation.reported_date >= (now - timedelta(hours=24))).count()
    last_30d = base_query.filter(Observation.reported_date >= (now - timedelta(days=30))).count()
    total = base_query.count()

    timeline_date = func.date(Observation.reported_date).label("date")
    timeline_query = db.query(timeline_date, func.count(Observation.id).label("count"))
    timeline_query = apply_observation_date_filters(timeline_query, from_date, to_date)
    timeline_rows = (
        timeline_query.group_by(timeline_date)
        .order_by(timeline_date.asc())
        .all()
    )

    return ObservationStatsResponse(
        top_risk_categories=grouped_observation_counts(
            db, Observation.risk_category, from_date, to_date
        ),
        area_details=grouped_observation_counts(
            db, Observation.area_of_observation, from_date, to_date
        ),
        operational_activities=grouped_observation_counts(
            db, Observation.operational_activity, from_date, to_date
        ),
        status_distribution=grouped_observation_counts(
            db, Observation.status, from_date, to_date
        ),
        timeline=[
            ObservationTimelinePoint(date=row.date, count=row.count)
            for row in timeline_rows
        ],
        summary_stats=ObservationSummaryStats(
            last_24h=last_24h,
            last_30d=last_30d,
            closed_on_time=closed_on_time,
            overdue=overdue,
            total=total,
        ),
        near_misses=near_misses,
    )


@router.get("/api/observation-factors/primary", response_model=List[ObservationFactorOption])
def get_primary_observation_factors(db: Session = Depends(get_db)):
    rows = (
        db.query(ObservationReviewFactor)
        .filter(ObservationReviewFactor.type == "primary_factor")
        .order_by(ObservationReviewFactor.sort_order, ObservationReviewFactor.id)
        .all()
    )
    return [ObservationFactorOption(id=row.id, label=row.value) for row in rows]


@router.get(
    "/api/observation-factors/{primary_id}",
    response_model=ObservationFactorOptionsResponse,
)
def get_observation_factor_options(primary_id: int, db: Session = Depends(get_db)):
    preconditions = (
        db.query(ObservationReviewFactor)
        .filter(
            ObservationReviewFactor.type == "precondition",
            ObservationReviewFactor.parent_id == primary_id,
        )
        .order_by(ObservationReviewFactor.sort_order, ObservationReviewFactor.id)
        .all()
    )
    underlying_causes = (
        db.query(ObservationReviewFactor)
        .filter(
            ObservationReviewFactor.type == "underlying_cause",
            ObservationReviewFactor.parent_id == primary_id,
        )
        .order_by(ObservationReviewFactor.sort_order, ObservationReviewFactor.id)
        .all()
    )

    return ObservationFactorOptionsResponse(
        preconditions=[
            ObservationFactorOption(id=row.id, label=row.value) for row in preconditions
        ],
        underlying_causes=[
            ObservationFactorOption(id=row.id, label=row.value) for row in underlying_causes
        ],
    )


@router.get("/api/observations/", response_model=ObservationListResponse)
def list_observations(
    observation_ref: str | None = None,
    department: str | None = None,
    operational_activity: str | None = None,
    status: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Observation)

    if observation_ref:
        query = query.filter(Observation.observation_ref.ilike(f"%{observation_ref.strip()}%"))
    if department:
        query = query.filter(Observation.department.ilike(f"%{department.strip()}%"))
    if operational_activity:
        query = query.filter(
            Observation.operational_activity.ilike(f"%{operational_activity.strip()}%")
        )
    if status:
        query = query.filter(Observation.status.ilike(status.strip()))
    query = apply_observation_date_filters(query, from_date, to_date)

    total = query.count()
    rows = (
        query.order_by(desc(Observation.reported_date), desc(Observation.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        ObservationListItem(
            observation_ref=row.observation_ref,
            reported_by_name=row.reported_by,
            designation=row.designation,
            reported_date=row.reported_date,
            area_of_observation=row.area_of_observation,
            sub_area=row.sub_area,
            observation_group=row.observation_group,
            observation_type=row.observation_type,
            status=row.status,
        )
        for row in rows
    ]

    return ObservationListResponse(total=total, items=items)


@router.get("/api/observations_details", response_model=ObservationResponse)
def get_observation(observation_ref: str, db: Session = Depends(get_db)):
    observation = (
        db.query(Observation)
        .filter(Observation.observation_ref == observation_ref.strip().upper())
        .first()
    )

    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    return observation


@router.get("/api/observationReviewAI", include_in_schema=False)
@router.get("/api/observaitonReviewAI")
def get_observation_review_ai(
    observation_id: str = Query(
        ...,
        description="Observation table id or observation_ref, for example 123 or OBS123456789",
    ),
    db: Session = Depends(get_db),
):
    observation_identifier = observation_id.strip()
    if observation_identifier.isdigit():
        observation = (
            db.query(Observation)
            .filter(Observation.id == int(observation_identifier))
            .first()
        )
    else:
        observation = (
            db.query(Observation)
            .filter(Observation.observation_ref == observation_identifier.upper())
            .first()
        )

    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    from ai_services.observation_gemini_service import analyze_observation_review

    return analyze_observation_review(observation_to_ai_payload(observation), db)


@router.post("/api/observation_review", response_model=ObservationReviewResponse)
def create_observation_review(
    data: ObservationReviewCreate,
    observation_ref: str = Query(..., description="Observation reference, for example OBS123456789"),
    db: Session = Depends(get_db),
):
    observation = (
        db.query(Observation)
        .filter(Observation.observation_ref == observation_ref.strip().upper())
        .first()
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    unsafe_abc = data.unsafe_abc[0] if data.unsafe_abc else None
    review = (
        db.query(ObservationReview)
        .filter(ObservationReview.observation_id == observation.id)
        .order_by(desc(ObservationReview.id))
        .first()
    )
    review_values = {
        "review_mode": data.review_mode,
        "review_comments": data.review_comments,
        "next_action": data.next_action,
        "primary_factor_id": unsafe_abc.primary_factor if unsafe_abc else None,
        "precondition_id": unsafe_abc.precondition if unsafe_abc else None,
        "underlying_cause_id": unsafe_abc.underlying_cause if unsafe_abc else None,
        "cause_description": unsafe_abc.cause if unsafe_abc else None,
        "reviewed_by": 10_000 + randbelow(90_000),
        "reviewed_at": datetime.utcnow(),
    }

    if review:
        for field, value in review_values.items():
            setattr(review, field, value)
    else:
        review = ObservationReview(
            observation_id=observation.id,
            **review_values,
        )
        db.add(review)

    if data.next_action.strip().lower() == "close":
        observation.status = "Closed"

    try:
        db.commit()
        db.refresh(review)
        db.refresh(observation)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create observation review")

    return ObservationReviewResponse(
        id=review.id,
        observation_id=review.observation_id,
        observation_ref=observation.observation_ref,
        review_mode=review.review_mode,
        review_comments=review.review_comments,
        next_action=review.next_action,
        primary_factor_id=review.primary_factor_id,
        precondition_id=review.precondition_id,
        underlying_cause_id=review.underlying_cause_id,
        cause_description=review.cause_description,
        reviewed_by=review.reviewed_by,
        reviewed_at=review.reviewed_at,
        observation_status=observation.status,
    )


@router.post("/api/newObservation/", response_model=ObservationResponse)
def create_observation(data: ObservationCreate, db: Session = Depends(get_db)):
    observation_data = data.model_dump(exclude={"reported_time"}, exclude_none=True)
    observation_data["reported_date"] = datetime.combine(data.reported_date, data.reported_time)

    observation = Observation(
        observation_ref=generate_observation_ref(db),
        status="New",
        **observation_data,
    )

    try:
        db.add(observation)
        db.commit()
        db.refresh(observation)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create observation")

    return observation
