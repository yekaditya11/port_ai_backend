from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime, date, time


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


# --- Involved Person Schemas ---

class InvolvedPersonCreate(BaseModel):
    worker_type: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    employee_id: Optional[str] = None
    age: Optional[int] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    particulars: Optional[str] = None

class InvolvedPersonResponse(BaseModel):
    id: int
    worker_type: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    employee_id: Optional[str] = None
    age: Optional[int] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    particulars: Optional[str] = None

    class Config:
        from_attributes = True


# --- Inspection Schemas ---

class WitnessCreate(BaseModel):
    worker_type: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    testimony: Optional[str] = None

class WitnessResponse(BaseModel):
    id: int
    worker_type: Optional[str] = None
    person_id: Optional[int] = None
    person_name: Optional[str] = None
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    testimony: Optional[str] = None

    class Config:
        from_attributes = True

class EquipmentInvolvedCreate(BaseModel):
    ownership_type: str = "Owned"
    equipment_id: Optional[int] = None
    company_name: Optional[str] = None
    equipment_ext_id: Optional[str] = None
    operator_name: Optional[str] = None
    equipment_position: Optional[str] = None
    degree_of_damage: Optional[str] = None
    is_predominant: bool = False

class EquipmentInvolvedResponse(BaseModel):
    id: int
    ownership_type: str
    equipment_id: Optional[int] = None
    company_name: Optional[str] = None
    equipment_ext_id: Optional[str] = None
    operator_name: Optional[str] = None
    equipment_position: Optional[str] = None
    degree_of_damage: Optional[str] = None
    is_predominant: bool

    class Config:
        from_attributes = True

class EnvironmentalDetailSchema(BaseModel):
    sensitive_area: Optional[bool] = None
    sensitive_remarks: Optional[str] = None
    remediation_required: Optional[bool] = None
    remediation_remarks: Optional[str] = None

    class Config:
        from_attributes = True

class TaskConditionSchema(BaseModel):
    roster_shift: Optional[str] = None
    traffic_volume: Optional[str] = None
    traffic_flow: Optional[str] = None
    lighting_condition: Optional[str] = None
    road_surface: Optional[str] = None

    class Config:
        from_attributes = True

class PermitDetailSchema(BaseModel):
    work_permit_obtained: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


# --- Investigation Schemas ---

class InvestigationTeamSchema(BaseModel):
    lead_investigator_id: Optional[int] = None
    team_members: Optional[List[str]] = []

    class Config:
        from_attributes = True

class SequenceOfEventCreate(BaseModel):
    phase: str
    event_date: Optional[datetime] = None
    event_time: Optional[str] = None
    description: Optional[str] = None
    is_main_event: Optional[bool] = False

class SequenceOfEventResponse(SequenceOfEventCreate):
    id: int
    class Config:
        from_attributes = True

class PeepoCreate(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    description: Optional[str] = None

class PeepoResponse(PeepoCreate):
    id: int
    class Config:
        from_attributes = True

class InvestigationAnalysisCreate(BaseModel):
    absent_failed_barriers: Optional[str] = None
    immediate_cause: Optional[str] = None
    precondition: Optional[str] = None
    underlying_cause: Optional[str] = None

class InvestigationAnalysisResponse(InvestigationAnalysisCreate):
    id: int
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
    risk_category: Optional[List[str]] = None
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
    work_activity_classification: Optional[str] = None
    reported_by_id: Optional[int] = None
    reported_to_id: Optional[int] = None
    is_regulatory_notification: Optional[bool] = False
    regulatory_notifiable: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewer_comments: Optional[str] = None
    reported_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    attachments: Optional[List[AttachmentCreate]] = []
    involved_persons: Optional[List[InvolvedPersonCreate]] = []

    @field_validator(
        "shift_manager_id", "shift_superintendent_id", "reported_by_id", "reported_to_id",
        "reported_date", "incident_date",
        mode="before"
    )
    @classmethod
    def empty_string_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and (v.strip() == "" or v == "Select"):
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
    risk_category: Optional[List[str]] = None
    actual_severity: Optional[str] = None
    potential_severity: Optional[str] = None
    critical_incident: Optional[str] = None
    shift: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    classification: Optional[str] = None
    work_activity_classification: Optional[str] = None
    reportable: Optional[str] = None
    recordable: Optional[str] = None
    description: Optional[str] = None
    immediate_action: Optional[str] = None
    is_regulatory_notification: Optional[bool] = False
    regulatory_notifiable: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewer_comments: Optional[str] = None
    reported_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    priority: Optional[str] = None
    created_at: Optional[datetime] = None
    attachments: Optional[List[AttachmentResponse]] = []
    involved_persons: Optional[List[InvolvedPersonResponse]] = []
    witnesses: Optional[List[WitnessResponse]] = []
    equipment_involved: Optional[List[EquipmentInvolvedResponse]] = []
    environmental_detail: Optional[EnvironmentalDetailSchema] = None
    task_condition: Optional[TaskConditionSchema] = None
    permit_detail: Optional[PermitDetailSchema] = None
    investigation_comments: Optional[str] = None
    investigation_team: Optional[InvestigationTeamSchema] = None
    sequence_of_events: Optional[List[SequenceOfEventResponse]] = []
    peepos: Optional[List[PeepoResponse]] = []
    investigation_analyses: Optional[List[InvestigationAnalysisResponse]] = []

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    total: int
    items: List[IncidentResponse]


class StatusUpdate(BaseModel):
    status: str


class ObservationCreate(BaseModel):
    reported_date: date
    reported_time: time
    area_of_observation: str
    business_unit: str
    department: str
    designation: str
    operational_activity: str
    observation_group: str
    specific_detail: str
    description: str
    reporter_confirmation: bool

    video_feed: Optional[str] = None
    is_anonymous: bool = False
    near_miss: bool = False
    time_of_day: Optional[str] = None
    shift: Optional[str] = None
    operational_department: Optional[str] = None
    sub_area: Optional[str] = None
    reported_by: Optional[str] = None
    weather: Optional[str] = None
    observation_type: Optional[str] = None
    potential_severity: Optional[str] = None
    observation_category: Optional[str] = None
    hazard_category: Optional[str] = None
    risk_category: Optional[str] = None
    repeated_observation_number: Optional[str] = None
    involved_personnel: Optional[str] = None
    immediate_action: Optional[str] = None


class ObservationResponse(BaseModel):
    id: int
    observation_ref: str
    status: str
    reported_date: datetime
    video_feed: Optional[str] = None
    is_anonymous: bool
    near_miss: bool
    time_of_day: Optional[str] = None
    shift: Optional[str] = None
    operational_department: Optional[str] = None
    area_of_observation: str
    sub_area: Optional[str] = None
    reported_by: Optional[str] = None
    business_unit: str
    department: str
    designation: str
    weather: Optional[str] = None
    observation_type: Optional[str] = None
    operational_activity: str
    potential_severity: Optional[str] = None
    observation_category: Optional[str] = None
    hazard_category: Optional[str] = None
    observation_group: str
    specific_detail: str
    risk_category: Optional[str] = None
    repeated_observation_number: Optional[str] = None
    involved_personnel: Optional[str] = None
    description: str
    immediate_action: Optional[str] = None
    reporter_confirmation: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObservationListItem(BaseModel):
    observation_ref: str
    reported_by_name: Optional[str] = None
    designation: Optional[str] = None
    reported_date: datetime
    area_of_observation: str
    sub_area: Optional[str] = None
    observation_group: str
    observation_type: Optional[str] = None
    status: str


class ObservationListResponse(BaseModel):
    total: int
    items: List[ObservationListItem]


class ObservationStatsBucket(BaseModel):
    name: str
    value: int


class ObservationTimelinePoint(BaseModel):
    date: date
    count: int


class ObservationSummaryStats(BaseModel):
    last_24h: int
    last_30d: int
    closed_on_time: int
    overdue: int
    total: int


class ObservationStatsResponse(BaseModel):
    top_risk_categories: List[ObservationStatsBucket]
    area_details: List[ObservationStatsBucket]
    operational_activities: List[ObservationStatsBucket]
    status_distribution: List[ObservationStatsBucket]
    timeline: List[ObservationTimelinePoint]
    summary_stats: ObservationSummaryStats
    near_misses: int


class ObservationFactorOption(BaseModel):
    id: int
    label: str


class ObservationFactorOptionsResponse(BaseModel):
    preconditions: List[ObservationFactorOption]
    underlying_causes: List[ObservationFactorOption]


class ObservationUnsafeABC(BaseModel):
    primary_factor: Optional[int] = Field(default=None, alias="primaryFactor")
    precondition: Optional[int] = None
    underlying_cause: Optional[int] = Field(default=None, alias="underlyingCause")
    cause: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("primary_factor", "precondition", "underlying_cause", mode="before")
    @classmethod
    def empty_factor_id_to_none(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class ObservationReviewCreate(BaseModel):
    review_mode: str
    review_comments: Optional[str] = None
    next_action: str
    unsafe_abc: List[ObservationUnsafeABC] = Field(default_factory=list)


class ObservationReviewResponse(BaseModel):
    id: int
    observation_id: int
    observation_ref: str
    review_mode: str
    review_comments: Optional[str] = None
    next_action: str
    primary_factor_id: Optional[int] = None
    precondition_id: Optional[int] = None
    underlying_cause_id: Optional[int] = None
    cause_description: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: datetime
    observation_status: str


class IncidentUpdate(BaseModel):
    incident_type: Optional[List[str]] = None
    area_of_incident: Optional[str] = None
    sub_area: Optional[str] = None
    operational_activity: Optional[str] = None
    incident_group: Optional[List[str]] = None
    sub_group: Optional[List[str]] = None
    critical_incident: Optional[str] = None
    risk_category: Optional[List[str]] = None
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
    work_activity_classification: Optional[str] = None
    reported_by_id: Optional[int] = None
    reported_to_id: Optional[int] = None
    is_regulatory_notification: Optional[bool] = None
    regulatory_notifiable: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewer_comments: Optional[str] = None
    status: Optional[str] = None
    reported_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    priority: Optional[str] = None
    involved_persons: Optional[List[InvolvedPersonCreate]] = None
    witnesses: Optional[List[WitnessCreate]] = None
    equipment_involved: Optional[List[EquipmentInvolvedCreate]] = None
    environmental_detail: Optional[EnvironmentalDetailSchema] = None
    task_condition: Optional[TaskConditionSchema] = None
    permit_detail: Optional[PermitDetailSchema] = None
    investigation_comments: Optional[str] = None
    investigation_team: Optional[InvestigationTeamSchema] = None
    sequence_of_events: Optional[List[SequenceOfEventCreate]] = None
    peepos: Optional[List[PeepoCreate]] = None
    investigation_analyses: Optional[List[InvestigationAnalysisCreate]] = None

    class Config:
        from_attributes = True


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
