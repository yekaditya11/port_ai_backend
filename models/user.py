from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)

    users = relationship("User", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    employee_id = Column(String(50), nullable=True)
    designation = Column(String(200), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(String(100), nullable=True)

    department = relationship("Department", back_populates="users")
