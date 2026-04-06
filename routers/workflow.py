from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models.workflow import WorkflowEvent
from models.incident import Incident
from models.user import User

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


def format_workflow(wf, db: Session):
    """Enrich workflow with incident ref, group, status, and reviewer name."""
    incident = db.query(Incident).filter(Incident.id == wf.incident_id).first()
    reviewer = db.query(User).filter(User.id == wf.reviewer_id).first() if wf.reviewer_id else None

    def fmt_dt(dt):
        if not dt:
            return "--"
        return dt.strftime("%d %b %y | %H:%M")

    return {
        "id": wf.id,
        "incident_id": wf.incident_id,
        "incident_ref": incident.incident_ref if incident else "--",
        "incident_group": incident.incident_group if incident else "--",
        "incident_status": incident.status if incident else "--",
        "reviewer_name": f"{reviewer.name}({reviewer.id})" if reviewer else "--",
        "recorded_at": fmt_dt(wf.recorded_at),
        "reviewed_at": fmt_dt(wf.reviewed_at),
        "inspected_at": fmt_dt(wf.inspected_at),
        "investigated_at": fmt_dt(wf.investigated_at),
        "action_at": fmt_dt(wf.action_at),
        "resolved_at": fmt_dt(wf.resolved_at),
        "tat": wf.tat or "--"
    }


@router.get("/")
def list_workflow(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(WorkflowEvent)
    total = query.count()
    items = query.order_by(desc(WorkflowEvent.recorded_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": [format_workflow(i, db) for i in items]}


@router.get("/{incident_id}")
def get_workflow(incident_id: int, db: Session = Depends(get_db)):
    wf = db.query(WorkflowEvent).filter(WorkflowEvent.incident_id == incident_id).first()
    if not wf:
        return {"error": "No workflow found for this incident"}
    return format_workflow(wf, db)
