from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.dialects.postgresql import ARRAY
from .attachment import IncidentAttachment

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_ref = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="New")  # New/Review/Inspection/Investigation/Resolution/Closed

    # Dates
    reported_date = Column(DateTime, nullable=True)
    incident_date = Column(DateTime, nullable=True)

    # Location
    area_of_incident = Column(String(200), nullable=True)
    sub_area = Column(String(200), nullable=True)
    operational_activity = Column(String(200), nullable=True)

    # Classification
    incident_type = Column(ARRAY(String(100)), nullable=True)
    incident_group = Column(ARRAY(String(200)), nullable=True)
    sub_group = Column(ARRAY(String(200)), nullable=True)
    critical_incident = Column(String(10), nullable=True)
    risk_category = Column(ARRAY(String(200)), nullable=True)

    # Severity
    actual_severity = Column(String(50), nullable=True)
    potential_severity = Column(String(50), nullable=True)
    priority = Column(String(50), nullable=True)

    # People
    shift_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    shift_superintendent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reported_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Conditions
    weather = Column(String(100), nullable=True)
    sea_state = Column(String(100), nullable=True)
    shift = Column(String(50), nullable=True)
    time_of_day = Column(String(50), nullable=True)
    lighting_source = Column(String(200), nullable=True)

    # Shipping
    shipping_line = Column(String(200), nullable=True)
    container_number = Column(String(100), nullable=True)
    shipping_line_informed = Column(String(10), nullable=True)

    # Details
    uin_number = Column(String(100), nullable=True)
    incident_title = Column(String(500), nullable=True)
    reportable = Column(String(10), nullable=True)
    recordable = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    immediate_action = Column(Text, nullable=True)
    classification = Column(String(200), nullable=True)
    work_activity_classification = Column(String(100), nullable=True)
    cctv_footages = Column(String(500), nullable=True)

    # Regulatory & Reviewer Feedback
    is_regulatory_notification = Column(Boolean, default=False)
    regulatory_notifiable = Column(String(10), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    investigation_comments = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    shift_manager = relationship("User", foreign_keys=[shift_manager_id])
    shift_superintendent = relationship("User", foreign_keys=[shift_superintendent_id])
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    reported_to = relationship("User", foreign_keys=[reported_to_id])

    involved_persons = relationship("InvolvedPerson", back_populates="incident", cascade="all, delete-orphan")
    witnesses = relationship("Witness", back_populates="incident", cascade="all, delete-orphan")
    equipment_involved = relationship("EquipmentInvolved", back_populates="incident", cascade="all, delete-orphan")
    container_details = relationship("ContainerDetail", back_populates="incident", cascade="all, delete-orphan")
    environmental_detail = relationship("EnvironmentalDetail", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    task_condition = relationship("TaskCondition", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    permit_detail = relationship("PermitDetail", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="incident")
    workflow_event = relationship("WorkflowEvent", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    root_cause_analyses = relationship("RootCauseAnalysis", back_populates="incident", cascade="all, delete-orphan")
    attachments = relationship("IncidentAttachment", back_populates="incident", cascade="all, delete-orphan")
    investigation_team = relationship("InvestigationTeam", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    sequence_of_events = relationship("SequenceOfEvent", back_populates="incident", cascade="all, delete-orphan")
    peepos = relationship("Peepo", back_populates="incident", cascade="all, delete-orphan")
    investigation_analyses = relationship("InvestigationAnalysis", back_populates="incident", cascade="all, delete-orphan")
