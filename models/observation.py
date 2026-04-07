from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    observation_ref = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="New")

    reported_date = Column(DateTime, nullable=False)

    video_feed = Column(String(200), nullable=True)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    near_miss = Column(Boolean, nullable=False, default=False)

    time_of_day = Column(String(50), nullable=True)
    shift = Column(String(50), nullable=True)
    operational_department = Column(String(200), nullable=True)

    area_of_observation = Column(String(200), nullable=False)
    sub_area = Column(String(200), nullable=True)

    reported_by = Column(String(200), nullable=True)
    business_unit = Column(String(200), nullable=False)
    department = Column(String(200), nullable=False)
    designation = Column(String(200), nullable=False)

    weather = Column(String(100), nullable=True)
    observation_type = Column(String(100), nullable=True)
    operational_activity = Column(String(300), nullable=False)
    potential_severity = Column(String(50), nullable=True)
    observation_category = Column(String(200), nullable=True)
    hazard_category = Column(String(200), nullable=True)

    observation_group = Column(String(200), nullable=False)
    specific_detail = Column(Text, nullable=False)
    risk_category = Column(String(200), nullable=True)
    repeated_observation_number = Column(String(50), nullable=True)
    involved_personnel = Column(Text, nullable=True)

    description = Column(Text, nullable=False)
    immediate_action = Column(Text, nullable=True)

    reporter_confirmation = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class ObservationReview(Base):
    __tablename__ = "observation_reviews"

    id = Column(Integer, primary_key=True)
    observation_id = Column(
        Integer,
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_mode = Column(String(50), nullable=False)
    review_comments = Column(Text, nullable=True)
    next_action = Column(String(50), nullable=False)

    primary_factor_id = Column(
        Integer,
        ForeignKey("observation_review_factors.id", ondelete="SET NULL"),
        nullable=True,
    )
    precondition_id = Column(
        Integer,
        ForeignKey("observation_review_factors.id", ondelete="SET NULL"),
        nullable=True,
    )
    underlying_cause_id = Column(
        Integer,
        ForeignKey("observation_review_factors.id", ondelete="SET NULL"),
        nullable=True,
    )
    cause_description = Column(Text, nullable=True)

    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, server_default=func.now(), nullable=True)
