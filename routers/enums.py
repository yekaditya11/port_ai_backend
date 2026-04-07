from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.enums import EnumValue, ObservationEnumValue
from models.reference import SubArea, OperationalActivity, Equipment, ShippingLine
from models.user import User, Department

router = APIRouter(prefix="/api/enums", tags=["Enums & Dropdowns"])


@router.get("/all")
def get_all_enums(db: Session = Depends(get_db)):
    """Returns ALL enum categories in one payload — perfect for populating all dropdowns at once."""
    rows = db.query(EnumValue).order_by(EnumValue.category, EnumValue.sort_order).all()
    result = {}
    for row in rows:
        if row.category not in result:
            result[row.category] = []
        result[row.category].append({"value": row.value, "parent": row.parent_value})
    
    # Include Reference Data lists for convenience
    result["operational_activities"] = [
        {"name": r.name} for r in db.query(OperationalActivity).order_by(OperationalActivity.name).all()
    ]
    
    result["shipping_lines"] = [
        {"name": r.name} for r in db.query(ShippingLine).order_by(ShippingLine.name).all()
    ]
    
    result["equipment"] = [
        {"id": r.id, "name": r.name, "category": r.category} 
        for r in db.query(Equipment).order_by(Equipment.name).all()
    ]
    
    return result


@router.get("/observation-enums/all")
def get_all_observation_enums(db: Session = Depends(get_db)):
    """Returns all observation enum categories in one payload."""
    rows = (
        db.query(ObservationEnumValue)
        .order_by(ObservationEnumValue.category, ObservationEnumValue.sort_order, ObservationEnumValue.id)
        .all()
    )
    result = {}
    for row in rows:
        if row.category not in result:
            result[row.category] = []
        result[row.category].append({"value": row.value, "parent": row.parent_value})
    return result


@router.get("/observation-enums/{category}")
def get_observation_enum_by_category(
    category: str,
    parent: str = None,
    db: Session = Depends(get_db),
):
    """Get values for a specific observation enum category. Use ?parent=X for subgroups."""
    query = db.query(ObservationEnumValue).filter(ObservationEnumValue.category == category)
    if parent:
        query = query.filter(ObservationEnumValue.parent_value == parent)
    rows = query.order_by(ObservationEnumValue.sort_order, ObservationEnumValue.id).all()
    return {"category": category, "values": [r.value for r in rows]}


@router.get("/{category}")
def get_enum_by_category(category: str, parent: str = None, db: Session = Depends(get_db)):
    """Get values for a specific enum category. Use ?parent=X for subgroups."""
    query = db.query(EnumValue).filter(EnumValue.category == category)
    if parent:
        query = query.filter(EnumValue.parent_value == parent)
    rows = query.order_by(EnumValue.sort_order).all()
    return {"category": category, "values": [r.value for r in rows]}


@router.get("/reference/sub-areas")
def get_sub_areas(area: str = None, db: Session = Depends(get_db)):
    """Get sub-areas, optionally filtered by parent area."""
    query = db.query(SubArea)
    if area:
        query = query.filter(SubArea.area_name == area)
    rows = query.all()
    return [{"area": r.area_name, "sub_area": r.sub_area_name} for r in rows]


@router.get("/reference/operational-activities")
def get_operational_activities(db: Session = Depends(get_db)):
    rows = db.query(OperationalActivity).order_by(OperationalActivity.name).all()
    return [r.name for r in rows]


@router.get("/reference/equipment")
def get_equipment(db: Session = Depends(get_db)):
    rows = db.query(Equipment).order_by(Equipment.name).all()
    return [{"id": r.id, "name": r.name, "category": r.category} for r in rows]


@router.get("/reference/shipping-lines")
def get_shipping_lines(db: Session = Depends(get_db)):
    rows = db.query(ShippingLine).order_by(ShippingLine.name).all()
    return [r.name for r in rows]


@router.get("/reference/users")
def get_users(db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.name).all()
    return [{"id": r.id, "name": r.name, "employee_id": r.employee_id, "designation": r.designation} for r in rows]


@router.get("/reference/departments")
def get_departments(db: Session = Depends(get_db)):
    rows = db.query(Department).order_by(Department.name).all()
    return [{"id": r.id, "name": r.name} for r in rows]
