from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from database import get_db
from models.incident import Incident
from models.attachment import IncidentAttachment
from models.workflow import WorkflowEvent
from models.user import User
from schemas.schemas import IncidentCreate, StatusUpdate
from datetime import datetime

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


def generate_incident_ref(db: Session) -> str:
    last = db.query(Incident).order_by(desc(Incident.incident_ref)).first()
    if last:
        # Extract numeric part handle potential non-integer issues safely
        try:
            num = int(last.incident_ref.replace("INC", "")) + 1
        except ValueError:
            num = 3280781
    else:
        num = 3280781
    return f"INC{num:08d}"


def format_incident(incident, db: Session):
    """Enrich incident with joined user names + workflow timestamps."""
    # Get user names
    def get_user_display(user_id):
        if not user_id:
            return "--"
        user = db.query(User).filter(User.id == user_id).first()
        return f"{user.name} ({user.employee_id})" if user else "--"

    def get_user_name(user_id):
        if not user_id:
            return "--"
        user = db.query(User).filter(User.id == user_id).first()
        return user.name if user else "--"

    # Get workflow timestamps
    workflow = db.query(WorkflowEvent).filter(WorkflowEvent.incident_id == incident.id).first()

    def fmt_dt(dt):
        if not dt:
            return "--"
        return dt.strftime("%d %b %y | %H:%M")

    return {
        "id": incident.id,
        "incident_ref": incident.incident_ref,
        "status": incident.status,
        "incident_title": incident.incident_title or "--",
        "incident_type": incident.incident_type or "--",
        "incident_group": incident.incident_group or "--",
        "sub_group": incident.sub_group or "--",
        "area_of_incident": incident.area_of_incident or "--",
        "sub_area": incident.sub_area or "--",
        "operational_activity": incident.operational_activity or "--",
        "risk_category": incident.risk_category or "--",
        "actual_severity": incident.actual_severity or "--",
        "potential_severity": incident.potential_severity or "--",
        "critical_incident": incident.critical_incident or "--",
        "shift": incident.shift or "--",
        "time_of_day": incident.time_of_day or "--",
        "weather": incident.weather or "--",
        "classification": incident.classification or "--",
        "reportable": incident.reportable or "--",
        "recordable": incident.recordable or "--",
        "description": incident.description or "--",
        "immediate_action": incident.immediate_action or "--",
        "reported_date": incident.reported_date.isoformat() if incident.reported_date else None,
        "incident_date": incident.incident_date.isoformat() if incident.incident_date else None,
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        # Enriched user names
        "shift_manager_name": get_user_display(incident.shift_manager_id),
        "shift_superintendent_name": get_user_display(incident.shift_superintendent_id),
        "reported_by_name": get_user_name(incident.reported_by_id),
        "reported_to_name": get_user_name(incident.reported_to_id),
        # Enriched workflow timestamps
        "reported_date_time": fmt_dt(incident.reported_date),
        "inspected_date_time": fmt_dt(workflow.inspected_at) if workflow else "--",
        "inspector_name": get_user_name(workflow.reviewer_id) if workflow else "--",
        "investigation_date_time": fmt_dt(workflow.investigated_at) if workflow else "--",
        "lead_investigator_name": get_user_name(workflow.reviewer_id) if workflow else "--",
    }


@router.post("/")
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    ref = generate_incident_ref(db)
    # Handle attachments separately to ensure correct model instantiation
    attachment_data = data.attachments or []
    incident_dict = data.model_dump(exclude={"attachments"}, exclude_none=True)
    
    incident = Incident(
        incident_ref=ref,
        status="New",
        **incident_dict
    )
    
    for attr in attachment_data:
        db_attr = IncidentAttachment(**attr.model_dump())
        incident.attachments.append(db_attr)
        
    db.add(incident)
    db.flush()

    workflow = WorkflowEvent(
        incident_id=incident.id,
        recorded_at=datetime.utcnow()
    )
    db.add(workflow)
    db.commit()
    db.refresh(incident)
    return format_incident(incident, db)


@router.get("/")
def list_incidents(
    status: str = None,
    incident_type: str = None,
    incident_group: str = None,
    shift: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Incident)

    if status:
        query = query.filter(Incident.status == status)
    if incident_type:
        query = query.filter(Incident.incident_type.contains([incident_type]))
    if incident_group:
        query = query.filter(Incident.incident_group.contains([incident_group]))
    if shift:
        query = query.filter(Incident.shift == shift)

    total = query.count()
    items = query.order_by(desc(Incident.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {"total": total, "items": [format_incident(i, db) for i in items]}


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return format_incident(incident, db)


@router.patch("/{incident_id}/status")
def update_status(incident_id: int, data: StatusUpdate, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = data.status

    workflow = db.query(WorkflowEvent).filter(WorkflowEvent.incident_id == incident_id).first()
    if workflow:
        now = datetime.utcnow()
        status_map = {
            "Review": "reviewed_at",
            "Inspection": "inspected_at",
            "Investigation": "investigated_at",
            "Resolution": "resolved_at",
        }
        field = status_map.get(data.status)
        if field:
            setattr(workflow, field, now)

    db.commit()
    return {"status": "updated", "new_status": data.status}
