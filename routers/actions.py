from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.action import Action
from models.incident import Incident
from models.user import User
from models.user import Department
from schemas.schemas import ActionCreate

router = APIRouter(prefix="/api/actions", tags=["Actions"])


def generate_action_ref(db: Session) -> str:
    last = db.query(Action).order_by(desc(Action.id)).first()
    if last:
        parts = last.action_ref.split("/")
        num = int(parts[-1]) + 1
    else:
        num = 3273
    return f"ACT/03/26/{num}"


def format_action(action, db: Session):
    """Enrich action with joined user and department names."""
    incident = db.query(Incident).filter(Incident.id == action.incident_id).first()
    owner = db.query(User).filter(User.id == action.owner_id).first() if action.owner_id else None
    created_by = db.query(User).filter(User.id == action.created_by_id).first() if action.created_by_id else None
    dept = db.query(Department).filter(Department.id == action.department_id).first() if action.department_id else None

    return {
        "id": action.id,
        "action_ref": action.action_ref,
        "incident_id": action.incident_id,
        "source_ref": incident.incident_ref if incident else "--",
        "description": action.description or "--",
        "module": action.module or "Incident",
        "ca_pa": action.ca_pa or "--",
        "hierarchy_of_control": action.hierarchy_of_control or "--",
        "priority": action.priority or "--",
        "owner_id": action.owner_id,
        "owner_name": f"{owner.name} ({owner.id})" if owner else "--",
        "department_id": action.department_id,
        "department_name": dept.name if dept else "--",
        "due_date": action.due_date.isoformat() if action.due_date else "--",
        "status": action.status or "New",
        "created_by_name": f"{created_by.name} ({created_by.id})" if created_by else "--",
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }


@router.post("/")
def create_action(data: ActionCreate, db: Session = Depends(get_db)):
    ref = generate_action_ref(db)
    action = Action(action_ref=ref, **data.model_dump(exclude_none=True))
    db.add(action)
    db.commit()
    db.refresh(action)
    return format_action(action, db)


@router.get("/")
def list_actions(
    status: str = None,
    incident_id: int = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(Action)
    if status:
        query = query.filter(Action.status == status)
    if incident_id:
        query = query.filter(Action.incident_id == incident_id)
    total = query.count()
    items = query.order_by(desc(Action.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": [format_action(i, db) for i in items]}


@router.patch("/{action_id}")
def update_action(action_id: int, status: str = None, db: Session = Depends(get_db)):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if status:
        action.status = status
    db.commit()
    return {"status": "updated"}
