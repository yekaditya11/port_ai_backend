from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base


class SubArea(Base):
    """Parent-child: Sub Areas depend on which Area is selected."""
    __tablename__ = "sub_areas"

    id = Column(Integer, primary_key=True, index=True)
    area_name = Column(String(200), nullable=False, index=True)
    sub_area_name = Column(String(200), nullable=False)


class OperationalActivity(Base):
    __tablename__ = "operational_activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False, unique=True)


class Equipment(Base):
    """Owned equipment available in the terminal."""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True)
    equipment_code = Column(String(50), nullable=True)


class ShippingLine(Base):
    __tablename__ = "shipping_lines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
