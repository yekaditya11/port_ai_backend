from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    action_ref = Column(String(50), unique=True, nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    rca_id = Column(Integer, ForeignKey("root_cause_analyses.id"), nullable=True)
    description = Column(Text, nullable=True)
    module = Column(String(50), default="Incident")
    ca_pa = Column(String(20), nullable=True)  # Corrective/Preventive
    hierarchy_of_control = Column(String(200), nullable=True)
    priority = Column(String(20), nullable=True)  # High/Medium/Low
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), default="New")  # New/In-progress/Overdue/Completed
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    incident = relationship("Incident", back_populates="actions")
    rca = relationship("RootCauseAnalysis", back_populates="actions")
    owner = relationship("User", foreign_keys=[owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    department = relationship("Department")
