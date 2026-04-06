from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class InvolvedPerson(Base):
    __tablename__ = "involved_persons"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    worker_type = Column(String(100), nullable=True)
    person_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    person_name = Column(String(200), nullable=True)
    employee_id = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    department = Column(String(200), nullable=True)
    designation = Column(String(200), nullable=True)
    particulars = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="involved_persons")
    person = relationship("User")


class Witness(Base):
    __tablename__ = "witnesses"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    worker_type = Column(String(100), nullable=True)
    person_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    testimony = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="witnesses")
    person = relationship("User")


class EquipmentInvolved(Base):
    __tablename__ = "equipment_involved"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    ownership_type = Column(String(20), nullable=False, default="Owned")  # Owned or Third Party
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)  # For owned
    company_name = Column(String(200), nullable=True)  # For third party
    equipment_ext_id = Column(String(100), nullable=True)
    operator_name = Column(String(200), nullable=True)
    equipment_position = Column(String(200), nullable=True)
    degree_of_damage = Column(String(50), nullable=True)
    is_predominant = Column(Boolean, default=False)

    incident = relationship("Incident", back_populates="equipment_involved")
    equipment = relationship("Equipment")


class ContainerDetail(Base):
    __tablename__ = "container_details"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    container_number = Column(String(100), nullable=True)
    damage_location = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="container_details")


class EnvironmentalDetail(Base):
    __tablename__ = "environmental_details"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, unique=True)
    sensitive_area = Column(Boolean, nullable=True)
    sensitive_remarks = Column(Text, nullable=True)
    remediation_required = Column(Boolean, nullable=True)
    remediation_remarks = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="environmental_detail")


class TaskCondition(Base):
    __tablename__ = "task_conditions"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, unique=True)
    roster_shift = Column(String(100), nullable=True)
    traffic_volume = Column(String(100), nullable=True)
    traffic_flow = Column(String(100), nullable=True)
    lighting_condition = Column(String(200), nullable=True)
    road_surface = Column(String(100), nullable=True)

    incident = relationship("Incident", back_populates="task_condition")


class PermitDetail(Base):
    __tablename__ = "permit_details"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, unique=True)
    work_permit_obtained = Column(String(10), nullable=True)
    remarks = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="permit_detail")
