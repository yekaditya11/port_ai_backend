"""
EnumValue table — stores ALL dropdown values in a single table.
Each row has a 'category' (e.g. 'incident_type') and a 'value' (e.g. 'Accident').
This avoids 18 separate tiny tables for simple dropdowns.
"""
from sqlalchemy import Column, Integer, String, Index
from database import Base


class EnumValue(Base):
    __tablename__ = "enum_values"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    value = Column(String(500), nullable=False)
    parent_value = Column(String(500), nullable=True)  # For subgroups mapped to groups
    sort_order = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_enum_category_value", "category", "value"),
    )


class ObservationEnumValue(Base):
    __tablename__ = "observation_enums"

    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)
    parent_value = Column(String(255), nullable=True)
    sort_order = Column(Integer, default=0)


class ObservationReviewFactor(Base):
    __tablename__ = "observation_review_factors"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=False)
    parent_id = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)
