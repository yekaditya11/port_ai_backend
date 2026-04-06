from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime, date


# --- Attachment Schemas ---

class AttachmentCreate(BaseModel):
    file_name: str
    file_url: str
    description: Optional[str] = None

class AttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_url: str
    description: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Incident Schemas ---

class IncidentCreate(BaseModel):
    incident_type: Optional[List[str]] = None
    area_of_incident: Optional[str] = None
    sub_area: Optional[str] = None
    operational_activity: Optional[str] = None
    incident_group: Optional[List[str]] = None
    sub_group: Optional[List[str]] = None
    critical_incident: Optional[str] = None
    risk_category: Optional[str] = None
    actual_severity: Optional[str] = None
    potential_severity: Optional[str] = None
    shift_manager_id: Optional[int] = None
    shift_superintendent_id: Optional[int] = None
    weather: Optional[str] = None
    sea_state: Optional[str] = None
    shift: Optional[str] = None
    time_of_day: Optional[str] = None
    shipping_line: Optional[str] = None
    container_number: Optional[str] = None
    shipping_line_informed: Optional[str] = None
    uin_number: Optional[str] = None
    incident_title: Optional[str] = None
    reportable: Optional[str] = None
    recordable: Optional[str] = None
    description: Optional[str] = None
    immediate_action: Optional[str] = None
    classification: Optional[str] = None
    reported_by_id: Optional[int] = None
    reported_to_id: Optional[int] = None
    reported_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    attachments: Optional[List[AttachmentCreate]] = []

    @field_validator(
        "shift_manager_id", "shift_superintendent_id", "reported_by_id", "reported_to_id",
        "reported_date", "incident_date",
        mode="before"
    )
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class IncidentResponse(BaseModel):
    id: int
    incident_ref: str
    status: str
    incident_title: Optional[str] = None
    incident_type: Optional[List[str]] = None
    incident_group: Optional[List[str]] = None
    sub_group: Optional[List[str]] = None
    area_of_incident: Optional[str] = None
    sub_area: Optional[str] = None
    operational_activity: Optional[str] = None
    risk_category: Optional[str] = None
    actual_severity: Optional[str] = None
    potential_severity: Optional[str] = None
    critical_incident: Optional[str] = None
    shift: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    classification: Optional[str] = None
    reportable: Optional[str] = None
    recordable: Optional[str] = None
    description: Optional[str] = None
    immediate_action: Optional[str] = None
    reported_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    attachments: Optional[List[AttachmentResponse]] = []

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    total: int
    items: List[IncidentResponse]


class StatusUpdate(BaseModel):
    status: str


# --- RCA Schemas ---

class RCACreate(BaseModel):
    incident_id: int
    process_type: Optional[str] = "Manual"
    root_cause: Optional[str] = None
    lead_investigator_id: Optional[int] = None


class RCAResponse(BaseModel):
    id: int
    rca_ref: str
    incident_id: int
    process_type: Optional[str] = None
    status: Optional[str] = None
    root_cause: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Action Schemas ---

class ActionCreate(BaseModel):
    incident_id: int
    rca_id: Optional[int] = None
    description: Optional[str] = None
    ca_pa: Optional[str] = None
    hierarchy_of_control: Optional[str] = None
    priority: Optional[str] = None
    owner_id: Optional[int] = None
    department_id: Optional[int] = None
    due_date: Optional[date] = None
    created_by_id: Optional[int] = None


class ActionResponse(BaseModel):
    id: int
    action_ref: str
    incident_id: int
    description: Optional[str] = None
    module: Optional[str] = None
    ca_pa: Optional[str] = None
    hierarchy_of_control: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Workflow Schemas ---

class WorkflowResponse(BaseModel):
    id: int
    incident_id: int
    recorded_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    inspected_at: Optional[datetime] = None
    investigated_at: Optional[datetime] = None
    action_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tat: Optional[str] = None

    class Config:
        from_attributes = True


# --- Enum Schemas ---

class EnumResponse(BaseModel):
    category: str
    values: List[str]


class UserResponse(BaseModel):
    id: int
    name: str
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    department_id: Optional[int] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True
