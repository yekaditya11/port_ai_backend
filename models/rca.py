from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RootCauseAnalysis(Base):
    __tablename__ = "root_cause_analyses"

    id = Column(Integer, primary_key=True, index=True)
    rca_ref = Column(String(50), unique=True, nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    process_type = Column(String(50), nullable=True, default="Manual")  # Manual/Automated
    status = Column(String(50), nullable=True, default="New")  # New/In-progress/Completed
    root_cause = Column(Text, nullable=True)
    lead_investigator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    incident = relationship("Incident", back_populates="root_cause_analyses")
    lead_investigator = relationship("User")
    actions = relationship("Action", back_populates="rca")
