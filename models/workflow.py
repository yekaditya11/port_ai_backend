from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False, unique=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps for each lifecycle stage
    recorded_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    inspected_at = Column(DateTime, nullable=True)
    investigated_at = Column(DateTime, nullable=True)
    action_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Turn-around time (stored as string like "08:23:15")
    tat = Column(String(20), nullable=True)

    incident = relationship("Incident", back_populates="workflow_event")
    reviewer = relationship("User")
