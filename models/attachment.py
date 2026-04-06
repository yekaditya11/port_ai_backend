from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class IncidentAttachment(Base):
    __tablename__ = "incident_attachments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)  # Can store Base64 or a local path/URL
    description = Column(Text, nullable=True)
    
    uploaded_at = Column(DateTime, server_default=func.now())

    # Relationship
    incident = relationship("Incident", back_populates="attachments")
