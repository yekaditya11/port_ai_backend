from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import get_db
from models.rca import RootCauseAnalysis
from models.incident import Incident
from models.action import Action
from models.user import User
from schemas.schemas import RCACreate

router = APIRouter(prefix="/api/rca", tags=["Root Cause Analysis"])


def generate_rca_ref(db: Session) -> str:
    last = db.query(RootCauseAnalysis).order_by(desc(RootCauseAnalysis.id)).first()
    if last:
        parts = last.rca_ref.split("/")
        num = int(parts[-1]) + 1
    else:
        num = 477
    return f"RCA/03/26/{num:04d}"


def format_rca(rca, db: Session):
    """Enrich RCA with parent incident data + action count + investigator name."""
    incident = db.query(Incident).filter(Incident.id == rca.incident_id).first()
    action_count = db.query(func.count(Action.id)).filter(Action.rca_id == rca.id).scalar() or 0

    investigator_name = "--"
    if rca.lead_investigator_id:
        user = db.query(User).filter(User.id == rca.lead_investigator_id).first()
        investigator_name = user.name if user else "--"

    return {
        "id": rca.id,
        "rca_ref": rca.rca_ref,
        "incident_id": rca.incident_id,
        "incident_ref": incident.incident_ref if incident else "--",
        "event_group": incident.incident_group if incident else "--",
        "operational_activity": incident.operational_activity if incident else "--",
        "event_type": incident.incident_type if incident else "--",
        "sub_area": incident.sub_area or "--" if incident else "--",
        "risk_category": incident.risk_category if incident else "--",
        "potential_severity": incident.potential_severity if incident else "--",
        "process_type": rca.process_type or "Manual",
        "status": rca.status or "New",
        "root_cause": rca.root_cause or "--",
        "action_count": action_count,
        "lead_investigator_name": investigator_name,
        "module": "Incident",
        "event_date_time": incident.incident_date.strftime("%d %b %y | %H:%M") if incident and incident.incident_date else "--",
        "created_at": rca.created_at.isoformat() if rca.created_at else None,
    }


@router.post("/")
def create_rca(data: RCACreate, db: Session = Depends(get_db)):
    ref = generate_rca_ref(db)
    rca = RootCauseAnalysis(rca_ref=ref, **data.model_dump(exclude_none=True))
    db.add(rca)
    db.commit()
    db.refresh(rca)
    return format_rca(rca, db)


@router.get("/")
def list_rca(status: str = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    query = db.query(RootCauseAnalysis)
    if status:
        query = query.filter(RootCauseAnalysis.status == status)
    total = query.count()
    items = query.order_by(desc(RootCauseAnalysis.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": [format_rca(i, db) for i in items]}


@router.get("/{rca_id}")
def get_rca(rca_id: int, db: Session = Depends(get_db)):
    rca = db.query(RootCauseAnalysis).filter(RootCauseAnalysis.id == rca_id).first()
    if not rca:
        raise HTTPException(status_code=404, detail="RCA not found")
    return format_rca(rca, db)


@router.patch("/{rca_id}")
def update_rca(rca_id: int, root_cause: str = None, status: str = None, db: Session = Depends(get_db)):
    rca = db.query(RootCauseAnalysis).filter(RootCauseAnalysis.id == rca_id).first()
    if not rca:
        raise HTTPException(status_code=404, detail="RCA not found")
    if root_cause:
        rca.root_cause = root_cause
    if status:
        rca.status = status
    db.commit()
    return {"status": "updated"}
