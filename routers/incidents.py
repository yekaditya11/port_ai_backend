from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from database import get_db
from models.incident import Incident
from models.attachment import IncidentAttachment
from models.workflow import WorkflowEvent
from models.user import User
from models.incident_details import (
    InvolvedPerson, 
    Witness, 
    EquipmentInvolved, 
    EnvironmentalDetail, 
    TaskCondition, 
    PermitDetail,
    InvestigationTeam,
    SequenceOfEvent,
    Peepo,
    InvestigationAnalysis
)
from schemas.schemas import IncidentCreate, StatusUpdate, IncidentUpdate
from datetime import datetime
from ai_services.gemini_service import analyze_media

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

try:
    import multipart  # noqa: F401
    MULTIPART_INSTALLED = True
except ImportError:
    MULTIPART_INSTALLED = False


if MULTIPART_INSTALLED:
    @router.post("/analyze")
    async def analyze_incident(
        files: List[UploadFile] = File(...),
        description: str = Form(None),
        db: Session = Depends(get_db)
    ):
        """Analyze multiple uploaded photo/video/audio with Gemini AI for form population."""
        media_data = []
        for file in files:
            file_bytes = await file.read()
            media_data.append((file_bytes, file.content_type))

        result = analyze_media(media_data, db, user_context=description or "")
        return result
else:
    @router.post("/analyze")
    async def analyze_incident_unavailable():
        raise HTTPException(
            status_code=503,
            detail="AI analysis is unavailable. Install `python-multipart` and `google-genai` in the active virtual environment.",
        )


@router.get("/refs")
def get_incident_refs(db: Session = Depends(get_db)):
    """Returns all unique incident_ref values sorted descending."""
    # Getting only the incident_ref strings, sorted.
    results = db.query(Incident.incident_ref).order_by(desc(Incident.incident_ref)).all()
    return [r[0] for r in results]


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
        "involved_persons": [
            {
                "id": p.id,
                "worker_type": p.worker_type,
                "person_id": p.person_id,
                "person_name": p.person_name,
                "employee_id": p.employee_id,
                "age": p.age,
                "department": p.department,
                "designation": p.designation,
                "particulars": p.particulars
            } for p in incident.involved_persons
        ],
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
        "work_activity_classification": incident.work_activity_classification or "--",
        "reportable": incident.reportable or "--",
        "recordable": incident.recordable or "--",
        "description": incident.description or "--",
        "immediate_action": incident.immediate_action or "--",
        "reported_date": incident.reported_date.isoformat() if incident.reported_date else None,
        "incident_date": incident.incident_date.isoformat() if incident.incident_date else None,
        "priority": incident.priority or "--",
        "created_at": incident.created_at.isoformat() if incident.created_at else None,
        "witnesses": [
            {
                "id": w.id,
                "worker_type": w.worker_type,
                "person_id": w.person_id,
                "person_name": get_user_name(w.person_id),
                "employee_id": db.query(User).filter(User.id == w.person_id).first().employee_id if w.person_id else "--",
                "testimony": w.testimony
            } for w in incident.witnesses
        ],
        "equipment_involved": [
            {
                "id": e.id,
                "ownership_type": e.ownership_type,
                "equipment_id": e.equipment_id,
                "company_name": e.company_name,
                "equipment_ext_id": e.equipment_ext_id,
                "operator_name": e.operator_name,
                "equipment_position": e.equipment_position,
                "degree_of_damage": e.degree_of_damage,
                "is_predominant": e.is_predominant
            } for e in incident.equipment_involved
        ],
        "environmental_detail": {
            "sensitive_area": incident.environmental_detail.sensitive_area if incident.environmental_detail else None,
            "sensitive_remarks": incident.environmental_detail.sensitive_remarks if incident.environmental_detail else None,
            "remediation_required": incident.environmental_detail.remediation_required if incident.environmental_detail else None,
            "remediation_remarks": incident.environmental_detail.remediation_remarks if incident.environmental_detail else None
        } if incident.environmental_detail else None,
        "task_condition": {
            "roster_shift": incident.task_condition.roster_shift if incident.task_condition else None,
            "traffic_volume": incident.task_condition.traffic_volume if incident.task_condition else None,
            "traffic_flow": incident.task_condition.traffic_flow if incident.task_condition else None,
            "lighting_condition": incident.task_condition.lighting_condition if incident.task_condition else None,
            "road_surface": incident.task_condition.road_surface if incident.task_condition else None
        } if incident.task_condition else None,
        "permit_detail": {
            "work_permit_obtained": incident.permit_detail.work_permit_obtained if incident.permit_detail else None,
            "remarks": incident.permit_detail.remarks if incident.permit_detail else None
        } if incident.permit_detail else None,
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
        "investigation_comments": incident.investigation_comments,
        "investigation_team": {
            "lead_investigator_id": incident.investigation_team.lead_investigator_id if incident.investigation_team else None,
            "team_members": incident.investigation_team.team_members if incident.investigation_team else []
        } if incident.investigation_team else None,
        "sequence_of_events": [
            {
                "id": s.id,
                "phase": s.phase,
                "event_date": s.event_date.isoformat() if s.event_date else None,
                "event_time": s.event_time,
                "description": s.description,
                "is_main_event": s.is_main_event
            } for s in incident.sequence_of_events
        ],
        "peepos": [
            {
                "id": p.id,
                "category": p.category,
                "sub_category": p.sub_category,
                "description": p.description
            } for p in incident.peepos
        ],
        "investigation_analyses": [
            {
                "id": a.id,
                "absent_failed_barriers": a.absent_failed_barriers,
                "immediate_cause": a.immediate_cause,
                "precondition": a.precondition,
                "underlying_cause": a.underlying_cause
            } for a in incident.investigation_analyses
        ],
    }


@router.post("/")
def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    ref = generate_incident_ref(db)
    # Handle collections separately to ensure correct model instantiation
    attachment_data = data.attachments or []
    involved_data = data.involved_persons or []
    
    # Exclude relations from the initial dict to avoid SQLAlchemy "dict as relationship" error
    incident_dict = data.model_dump(
        exclude={"attachments", "involved_persons", "sequence_of_events", "peepos", "investigation_analyses", "investigation_team"}, 
        exclude_none=True
    )
    
    incident = Incident(
        incident_ref=ref,
        status="New",
        **incident_dict
    )
    
    for attr in attachment_data:
        db_attr = IncidentAttachment(**attr.model_dump())
        incident.attachments.append(db_attr)
        
    for person in involved_data:
        db_person = InvolvedPerson(**person.model_dump())
        incident.involved_persons.append(db_person)

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
    incident_ref: str = None,
    start_date: str = None,
    end_date: str = None,
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
    if incident_ref:
        query = query.filter(Incident.incident_ref.ilike(f"%{incident_ref}%"))
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.filter(Incident.incident_date >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            # Set end_dt to the end of the day if it's just a date
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if end_dt.hour == 0 and end_dt.minute == 0:
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Incident.incident_date <= end_dt)
        except ValueError:
            pass

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
    update_workflow_status(incident_id, data.status, db)
    db.commit()
    return {"status": "updated", "new_status": data.status}


@router.put("/{incident_id}")
def update_incident(incident_id: int, data: IncidentUpdate, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Update all fields provided in the body
    update_data = data.dict(exclude_unset=True)
    
    # Special handling for status to update workflow timestamps
    if "status" in update_data and update_data["status"] != incident.status:
        update_workflow_status(incident_id, update_data["status"], db)

    # 1. Handle nested collections (Involved Persons, Witnesses, Equipment)
    # Re-creation strategy for simplicity
    if "involved_persons" in update_data:
        involved_list = update_data.pop("involved_persons")
        db.query(InvolvedPerson).filter(InvolvedPerson.incident_id == incident_id).delete()
        if involved_list:
            for p in involved_list:
                db_p = InvolvedPerson(incident_id=incident_id, **p)
                db.add(db_p)

    if "witnesses" in update_data:
        witness_list = update_data.pop("witnesses")
        db.query(Witness).filter(Witness.incident_id == incident_id).delete()
        if witness_list:
            for w in witness_list:
                db_w = Witness(incident_id=incident_id, **w)
                db.add(db_w)

    if "equipment_involved" in update_data:
        equipment_list = update_data.pop("equipment_involved")
        db.query(EquipmentInvolved).filter(EquipmentInvolved.incident_id == incident_id).delete()
        if equipment_list:
            for e in equipment_list:
                db_e = EquipmentInvolved(incident_id=incident_id, **e)
                db.add(db_e)

    if "sequence_of_events" in update_data:
        soe_list = update_data.pop("sequence_of_events")
        db.query(SequenceOfEvent).filter(SequenceOfEvent.incident_id == incident_id).delete()
        if soe_list:
            for s in soe_list:
                db_s = SequenceOfEvent(incident_id=incident_id, **s)
                db.add(db_s)

    if "peepos" in update_data:
        peepo_list = update_data.pop("peepos")
        db.query(Peepo).filter(Peepo.incident_id == incident_id).delete()
        if peepo_list:
            for p in peepo_list:
                db_p = Peepo(incident_id=incident_id, **p)
                db.add(db_p)

    if "investigation_analyses" in update_data:
        ia_list = update_data.pop("investigation_analyses")
        db.query(InvestigationAnalysis).filter(InvestigationAnalysis.incident_id == incident_id).delete()
        if ia_list:
            for ia in ia_list:
                db_ia = InvestigationAnalysis(incident_id=incident_id, **ia)
                db.add(db_ia)

    if "investigation_team" in update_data:
        it_data = update_data.pop("investigation_team")
        if incident.investigation_team:
            for k, v in it_data.items():
                setattr(incident.investigation_team, k, v)
        elif it_data:
            db_it = InvestigationTeam(incident_id=incident_id, **it_data)
            db.add(db_it)

    # 2. Handle nested objects (Environmental, Task Condition, Permit)
    if "environmental_detail" in update_data:
        env_data = update_data.pop("environmental_detail")
        if incident.environmental_detail:
            for k, v in env_data.items():
                setattr(incident.environmental_detail, k, v)
        elif env_data:
            db_env = EnvironmentalDetail(incident_id=incident_id, **env_data)
            db.add(db_env)

    if "task_condition" in update_data:
        tc_data = update_data.pop("task_condition")
        if incident.task_condition:
            for k, v in tc_data.items():
                setattr(incident.task_condition, k, v)
        elif tc_data:
            db_tc = TaskCondition(incident_id=incident_id, **tc_data)
            db.add(db_tc)

    if "permit_detail" in update_data:
        pd_data = update_data.pop("permit_detail")
        if incident.permit_detail:
            for k, v in pd_data.items():
                setattr(incident.permit_detail, k, v)
        elif pd_data:
            db_pd = PermitDetail(incident_id=incident_id, **pd_data)
            db.add(db_pd)

    # 3. Handle remaining flat fields
    for key, value in update_data.items():
        setattr(incident, key, value)

    db.commit()
    db.refresh(incident)
    return format_incident(incident, db)


@router.post("/{incident_id}/audit")
def audit_incident(incident_id: int, db: Session = Depends(get_db)):
    """Triggers an AI-powered semantic audit for a specific incident report."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Format current data for AI context
    incident_data = format_incident(incident, db)
    
    # Perform the AI audit
    from ai_services.audit_service import perform_ai_audit
    results = perform_ai_audit(incident_data, db)
    
    return results


def update_workflow_status(incident_id: int, new_status: str, db: Session):
    workflow = db.query(WorkflowEvent).filter(WorkflowEvent.incident_id == incident_id).first()
    if workflow:
        now = datetime.utcnow()
        status_map = {
            "Review": "reviewed_at",
            "Inspection": "inspected_at",
            "Investigation": "investigated_at",
            "Resolution": "resolved_at",
        }
        field = status_map.get(new_status)
        if field:
            setattr(workflow, field, now)
