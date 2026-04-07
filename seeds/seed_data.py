"""
Seed data for the entire incident management system.
Populates: enum_values, departments, users, sub_areas, operational_activities, equipment, shipping_lines, and mock incidents.
"""
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from models.enums import EnumValue
from models.user import Department, User
from models.reference import SubArea, OperationalActivity, Equipment, ShippingLine
from models.incident import Incident
from models.rca import RootCauseAnalysis
from models.action import Action
from models.workflow import WorkflowEvent


def seed_all(db: Session):
    """Master seed function — call this once to populate everything."""

    # Check if already seeded
    if db.query(EnumValue).first():
        print("⚠️  Database already seeded. Skipping.")
        return

    print("🌱 Seeding database...")

    seed_enums(db)
    seed_departments(db)
    seed_users(db)
    seed_sub_areas(db)
    seed_operational_activities(db)
    seed_equipment(db)
    seed_shipping_lines(db)
    seed_incidents(db)

    db.commit()
    print("✅ Database seeded successfully!")


def seed_enums(db: Session):
    """Seed ALL enum/dropdown values from the enums file + missing ones."""

    enums = {
        # ===== FROM incident_module_enums.py =====
        "incident_type": [
            "Accident", "Asset Damage", "Environment", "Environmental Disaster",
            "Injury & Ill Health", "Near Miss", "Security", "Unspecified", "Vehicle Accident"
        ],
        "area_of_incident": [
            "Admin. Building", "Bilge Facility", "Bunkering Station", "Cargo Loading Dock",
            "CFS Yard", "Chemical Storage Area", "Container & General Cargo Berth",
            "Container Berth", "Container Freight Station", "Container Parking Yard",
            "Container Terminal B", "Container Yard", "Dockside Operations",
            "Dry cargo Warehouse", "Engineering Workshop", "Entire Terminal",
            "Fuel station", "Gate", "General Cargo Berth", "Hazardous Spill Bund Area",
            "IMDG Yard", "ITV Parking area", "Occupational Health Center",
            "Passenger Berth", "Port Dock No. 3", "Pumphouse", "RORO yard",
            "Security Main Gate", "Social Facility", "Storage Tank Farm",
            "Substation", "Tank farm", "TLF Loading point", "Warehouse",
            "Waste Reception Facility"
        ],
        "risk_category": [
            "Access Control Failure", "Accident", "Accident Risk", "Acts of Violence",
            "Chemical Exposure", "Collapse", "Collision", "Collision Damage",
            "Communication Failure", "Container Fall", "Crash/Hit", "Cut / Laceration",
            "Cut Injury", "Damage", "Drowning", "Electrical Hazard", "Electrical Shock",
            "Entanglement", "Environmental Damage", "Environmental Impacts/Pollution",
            "Environmental Pollution", "Equipment Damage", "Equipment Failure",
            "Explosion Risk", "Fall", "Fall From Height", "Falling Objects", "Fire",
            "Fire Hazard", "Fire Outbreak", "Human Error", "Human Errors", "Impact Injury",
            "Injury", "Machinery Breakdown", "Mechanical Failure", "Obstruction",
            "Operational Error", "Other", "Others", "Pollution", "Safety Hazard",
            "Slip", "Slip, Trip or Falls on Same Level", "Structural Collapse",
            "Structural Integrity", "Traffic Accident", "Trip", "Trip Hazard",
            "Truck Roll over", "Unauthorized Access", "Vehicle Rollover",
            "Visibility Problems"
        ],
        "severity_level": [
            "1-Negligible", "2-Minor", "3-Moderate", "4-Major", "5-Catastrophic"
        ],
        "critical_incident": ["No", "Yes"],
        "sea_state": [
            "Calm Rippled", "Calm-Glassy", "High", "Moderate", "Phenomenal",
            "Rough", "Slight", "Smooth wavelets", "Very High", "Very Rough"
        ],
        "incident_group": [
            "Defective Machinery", "Environmental Impact", "Equipment Failures",
            "Human Errors", "Impacting Health", "Infrastructure Damage",
            "Miscellaneous", "Operations management", "Safety Violations", "Security Breaches"
        ],
        "source_of_lighting": [
            "Daylight Full", "Daylight Partial", "Daylight Shadow",
            "Deck Lighting Adequate", "Deck Lighting Good", "Deck Lighting Poor",
            "In. Electric Lighting Poor", "Int. El. Lighting Adequate",
            "Internal El. Lighting Good", "Moonlight Full", "Moonlight Partial",
            "Night Darkness", "Other", "Torchlight"
        ],

        # ===== NEW ENUMS (Missing from the file) =====
        "incident_status": [
            "New", "Review", "Inspection", "Investigation", "Resolution", "Closed"
        ],
        "shift": ["Shift 1", "Shift 2", "Shift 3"],
        "time_of_day": ["Morning", "Afternoon", "Twilight", "Night"],
        "weather": [
            "Clear & Sunny", "Clean & Calm", "Cloudy", "Rainy",
            "Windy", "Stormy", "Foggy", "Humid", "Hot", "Cold"
        ],
        "worker_type": [
            "Company Employee", "Contractor", "Visitor", "Third Party", "Other"
        ],
        "yes_no_na": ["Yes", "No", "N/A"],
        "damage_location": [
            "Front", "Rear", "Left", "Right", "Top", "Bottom", "Internal", "Multiple"
        ],
        "degree_of_damage": ["Minor", "Moderate", "Major", "Total Loss"],
        "traffic_volume": ["Light", "Moderate", "Heavy", "Very Heavy"],
        "traffic_flow": ["Free Flow", "Restricted", "Congested", "Stopped"],
        "road_surface": ["Dry", "Wet", "Oily", "Rough", "Smooth", "Gravel", "Muddy"],
        "roster_shift": ["Day", "Night", "Rotating", "Extended"],
        "ca_pa": ["Corrective", "Preventive"],
        "hierarchy_of_control": [
            "Elimination", "Substitution", "Engineering Controls",
            "Administrative Controls", "PPE"
        ],
        "action_priority": ["High", "Medium", "Low"],
        "action_status": ["New", "In-progress", "Completed", "Overdue", "Cancelled"],
        "rca_process_type": ["Manual", "Automated"],
        "rca_status": ["New", "In-progress", "Completed"],
        "work_activity_classification": [
            "Work Related Incident", "Non-Work Related Incident",
            "Third Party Incident", "Visitor Incident"
        ],
    }

    # Seed subgroups (parent-child mapping)
    subgroups = {
        "Defective Machinery": ["Operating vehicles with NOGO items", "Others"],
        "Environmental Impact": [
            "Air pollution from vehicle emissions", "Contamination of water resources",
            "Improper waste disposal and management", "Oil and fuel spillages", "Others"
        ],
        "Equipment Failures": [
            "Damage to handling", "Lack of maintenance",
            "Machinery breakdowns and technical failures", "Malfunctioning vehicle components", "Others"
        ],
        "Human Errors": [
            "Inadequate training leading to mistakes", "Miscommunication between personnel",
            "Negligence in following standard protocols", "Non-compliance with safety regulations",
            "Others", "Unauthorized access to restricted areas", "Working without appropriate PPE"
        ],
        "Impacting Health": [
            "First aid requirements and treatments", "Medical emergencies on-site",
            "Minor injuries and accidents", "Occupational health issues", "Others"
        ],
        "Infrastructure Damage": [
            "Bad road surfaces and inadequate signage", "Collisions with barriers, gates, and structures",
            "Damage to terminal buildings", "Impact on electrical and utility infrastructure", "Others"
        ],
        "Miscellaneous": ["Others"],
        "Operations management": [
            "Cargo handling accidents", "Errors in loading and unloading",
            "Improper stacking of containers", "Incorrect terminal procedures", "Others"
        ],
        "Safety Violations": [
            "Inadequate barricading and safety protocols", "Others", "Overspeeding and reckless driving"
        ],
        "Security Breaches": [
            "Breaches in surveillance and monitoring", "Incidents related to illegal activities",
            "Others", "Theft and tampering of cargo"
        ],
    }

    # Insert flat enums
    order = 0
    for category, values in enums.items():
        for i, val in enumerate(values):
            db.add(EnumValue(category=category, value=val, sort_order=i))
            order += 1

    # Insert subgroups with parent mapping
    for parent, children in subgroups.items():
        for i, child in enumerate(children):
            db.add(EnumValue(category="incident_subgroup", value=child, parent_value=parent, sort_order=i))

    print(f"  ✅ Seeded {order} enum values + subgroups")


def seed_departments(db: Session):
    depts = [
        "HSE Operations", "Finance & Purchase", "Administration",
        "Port Operations", "Engineering & Maintenance", "Security", "Marine Operations"
    ]
    for name in depts:
        db.add(Department(name=name))
    db.flush()
    print(f"  ✅ Seeded {len(depts)} departments")


def seed_users(db: Session):
    hse = db.query(Department).filter(Department.name == "HSE Operations").first()
    fin = db.query(Department).filter(Department.name == "Finance & Purchase").first()
    adm = db.query(Department).filter(Department.name == "Administration").first()

    users = [
        User(id=104, name="Martin Debeloz", employee_id="IDA", designation="General Manager", department_id=hse.id, role="HSE Manager"),
        User(id=952, name="Ali Aladeq", employee_id="952", designation="Safety Officer", department_id=hse.id, role="HSE Operations"),
        User(id=445, name="Yusuf Honaz", employee_id="445", designation="Safety Engineer", department_id=hse.id, role="HSE Operations"),
        User(id=895, name="Shaia Waleed", employee_id="895", designation="HSE Coordinator", department_id=hse.id, role="HSE Operations"),
        User(id=703, name="Gazi Abbas", employee_id="703", designation="Safety Inspector", department_id=hse.id, role="HSE Operations"),
        User(id=3589, name="Asdasdas Asdasdas", employee_id="3589", designation="Analyst", department_id=fin.id, role="Finance"),
        User(id=837, name="Arpitha MG", employee_id="837", designation="Admin Officer", department_id=adm.id, role="Administration"),
        User(id=2563, name="Forhat Karacigay", employee_id="2563", designation="HSE Lead", department_id=hse.id, role="HSE Operations"),
        User(id=2196, name="Omar Kadir Ali", employee_id="2196", designation="Operations Supervisor", department_id=hse.id, role="HSE Operations"),
        User(id=8, name="Mak george", employee_id="8", designation="Port Worker", department_id=hse.id, role="HSE Operations"),
    ]
    for u in users:
        db.add(u)
    db.flush()
    print(f"  ✅ Seeded {len(users)} users")


def seed_sub_areas(db: Session):
    # User requested to keep subareas empty
    print("  ℹ️ Skipping sub-area mappings per requirement")
    pass


def seed_operational_activities(db: Session):
    activities = [
        "Administration /Office Tasks",
        "Berthing/Unberthing",
        "Bulk Cargo Operations",
        "Bulk Chemical Storage and Handling",
        "Bunkering Ops",
        "Cargo Handling",
        "Cleaning and Housekeeping",
        "Container Scanning",
        "Container Yard Operations",
        "Contractor Management",
        "Driving",
        "Electrical Work",
        "Equipment Maintenance",
        "Facility Maintenance",
        "Forklift Operations",
        "Gate Operations",
        "General Cargo Handling",
        "Hatch Cover Operation",
        "Hose Testing Activities",
        "Hot Work Activities",
        "Mooring Operation",
        "Others",
        "Pigging Operation",
        "Pumping Operation",
        "Rail Operations",
        "Reefer Operations",
        "RMG Operations",
        "RS Operations",
        "RTG Operations",
        "Tanker Lorry Filling ",
        "Vessel Berthing",
        "Vessel Operation"
    ]
    for name in activities:
        db.add(OperationalActivity(name=name))
    db.flush()
    print(f"  ✅ Seeded {len(activities)} operational activities")


def seed_equipment(db: Session):
    equip = [
        ("Reach Stacker", "Heavy"), ("Forklift", "Heavy"), ("STS Crane", "Heavy"),
        ("RTG Crane", "Heavy"), ("Trailer Truck", "Vehicle"), ("ITV", "Vehicle"),
        ("Mobile Crane", "Heavy"), ("Tug Boat", "Marine"), ("Pilot Boat", "Marine"),
        ("Fire Truck", "Emergency"), ("Ambulance", "Emergency"),
    ]
    for name, cat in equip:
        db.add(Equipment(name=name, category=cat))
    db.flush()
    print(f"  ✅ Seeded {len(equip)} equipment records")


def seed_shipping_lines(db: Session):
    lines = ["Maersk", "MSC", "CMA CGM", "Hapag-Lloyd", "COSCO", "ONE", "Evergreen", "Yang Ming"]
    for name in lines:
        db.add(ShippingLine(name=name))
    db.flush()
    print(f"  ✅ Seeded {len(lines)} shipping lines")


def seed_incidents(db: Session):
    """Seed the mock incidents from our frontend for immediate visual parity."""
    now = datetime.utcnow()

    incidents_data = [
        {
            "incident_ref": "INC03280780",
            "status": "Inspection",
            "incident_title": "Environmental Impact",
            "incident_type": ["Environment"],
            "incident_group": ["Environmental Impact"],
            "sub_group": ["Oil and fuel spillages"],
            "area_of_incident": "Bunkering Station",
            "sub_area": None,
            "operational_activity": "Bulk Chemical Storage and Handling",
            "risk_category": "Environmental Pollution",
            "actual_severity": "2-Minor",
            "potential_severity": "2-Minor",
            "critical_incident": "Yes",
            "shift": "Shift 2",
            "time_of_day": "Afternoon",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "shift_manager_id": 104,
            "reported_date": now - timedelta(days=9),
            "incident_date": now - timedelta(days=9),
        },
        {
            "incident_ref": "INC03280779",
            "status": "Review",
            "incident_title": "Infrastructure Damage",
            "incident_type": ["Unspecified"],
            "incident_group": ["Infrastructure Damage"],
            "sub_group": ["Bad road surfaces and inadequate signage"],
            "area_of_incident": "Admin. Building",
            "sub_area": None,
            "operational_activity": "Driving",
            "risk_category": "Obstruction",
            "actual_severity": "2-Minor",
            "potential_severity": "2-Minor",
            "critical_incident": "No",
            "shift": "Shift 3",
            "time_of_day": "Twilight",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "shift_manager_id": 104,
            "reported_date": now - timedelta(days=10),
            "incident_date": now - timedelta(days=10),
        },
        {
            "incident_ref": "INC03280778",
            "status": "Inspection",
            "incident_title": "Miscellaneous",
            "incident_type": ["Asset Damage"],
            "incident_group": ["Miscellaneous"],
            "sub_group": ["Others"],
            "area_of_incident": "Bunkering Station",
            "sub_area": None,
            "operational_activity": "Equipment Maintenance",
            "risk_category": "Fire",
            "actual_severity": "4-Major",
            "potential_severity": "4-Major",
            "shift": "Shift 2",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "reported_date": now - timedelta(days=10),
            "incident_date": now - timedelta(days=10),
        },
        {
            "incident_ref": "INC03280777",
            "status": "Review",
            "incident_title": "Impacting Health",
            "incident_type": ["Injury & Ill Health"],
            "incident_group": ["Impacting Health"],
            "sub_group": ["Minor injuries and accidents"],
            "area_of_incident": "Container Berth",
            "sub_area": None,
            "operational_activity": "Vessel Operation",
            "risk_category": "Cut / Laceration",
            "actual_severity": "2-Minor",
            "potential_severity": "2-Minor",
            "critical_incident": "No",
            "shift": "Shift 1",
            "time_of_day": "Night",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "shift_manager_id": 104,
            "reported_date": now - timedelta(days=11),
            "incident_date": now - timedelta(days=11),
        },
        {
            "incident_ref": "INC03280776",
            "status": "New",
            "incident_title": "Infrastructure Damage",
            "incident_type": ["Environmental Disaster"],
            "incident_group": ["Infrastructure Damage"],
            "area_of_incident": "Gate",
            "sub_area": None,
            "operational_activity": "Gate Operations",
            "risk_category": "Human Error",
            "actual_severity": "3-Moderate",
            "potential_severity": "3-Moderate",
            "shift": "Shift 2",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "reported_date": now - timedelta(days=11),
            "incident_date": now - timedelta(days=11),
        },
        {
            "incident_ref": "INC03280775",
            "status": "Inspection",
            "incident_title": "Operations management",
            "incident_type": ["Accident"],
            "incident_group": ["Operations management"],
            "area_of_incident": "Container Yard",
            "sub_area": None,
            "operational_activity": "Container Yard Operations",
            "risk_category": "Structural Collapse",
            "actual_severity": "4-Major",
            "potential_severity": "4-Major",
            "shift": "Shift 2",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "reported_date": now - timedelta(days=11),
            "incident_date": now - timedelta(days=11),
        },
        {
            "incident_ref": "INC03280774",
            "status": "Review",
            "incident_title": "Equipment Failures",
            "incident_type": ["Asset Damage"],
            "incident_group": ["Equipment Failures"],
            "sub_group": ["Machinery breakdowns and technical failures"],
            "area_of_incident": "CFS Yard",
            "sub_area": None,
            "operational_activity": "Equipment Maintenance",
            "risk_category": "Machinery Breakdown",
            "actual_severity": "2-Minor",
            "potential_severity": "2-Minor",
            "shift": "Shift 2",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "reported_date": now - timedelta(days=11),
            "incident_date": now - timedelta(days=11),
        },
        {
            "incident_ref": "INC03280773",
            "status": "Investigation",
            "incident_title": "Defective Machinery",
            "incident_type": ["Asset Damage"],
            "incident_group": ["Defective Machinery"],
            "area_of_incident": "Hazardous Spill Bund Area",
            "sub_area": None,
            "operational_activity": "RS Operations",
            "risk_category": "Vehicle Rollover",
            "actual_severity": "4-Major",
            "potential_severity": "4-Major",
            "shift": "Shift 2",
            "time_of_day": "Afternoon",
            "weather": "Clean & Calm",
            "classification": "Work Related Incident",
            "work_activity_classification": "Work Related Incident",
            "reported_by_id": 104,
            "reported_date": now - timedelta(days=12),
            "incident_date": now - timedelta(days=12),
        },
    ]

    for idata in incidents_data:
        inc = Incident(**idata)
        db.add(inc)
    db.flush()

    # Create workflow entries for each incident
    for inc in db.query(Incident).all():
        wf = WorkflowEvent(
            incident_id=inc.id,
            reviewer_id=104,
            recorded_at=inc.reported_date,
            reviewed_at=inc.reported_date + timedelta(minutes=5) if inc.status in ["Review", "Inspection", "Investigation", "Resolution"] else None,
            inspected_at=inc.reported_date + timedelta(minutes=10) if inc.status in ["Inspection", "Investigation", "Resolution"] else None,
            investigated_at=inc.reported_date + timedelta(minutes=30) if inc.status in ["Investigation", "Resolution"] else None,
            tat="08:23:15"
        )
        db.add(wf)

    # Create RCA records for some incidents
    rca_data = [
        {"rca_ref": "RCA/03/26/0482", "incident_id": 4, "process_type": "Manual", "status": "In-progress", "root_cause": "Uneven ground / trip hazards", "lead_investigator_id": 104},
        {"rca_ref": "RCA/03/26/0480", "incident_id": 5, "process_type": "Manual", "status": "New", "root_cause": "Perception error", "lead_investigator_id": 104},
        {"rca_ref": "RCA/03/26/0478", "incident_id": 6, "process_type": "Manual", "status": "In-progress", "root_cause": "Procedural gaps", "lead_investigator_id": 104},
        {"rca_ref": "RCA/03/26/0477", "incident_id": 7, "process_type": "Manual", "status": "In-progress", "root_cause": "Inadequate maintenance measures", "lead_investigator_id": 104},
    ]
    for rd in rca_data:
        db.add(RootCauseAnalysis(**rd))
    db.flush()

    # Create Actions
    hse = db.query(Department).filter(Department.name == "HSE Operations").first()
    fin = db.query(Department).filter(Department.name == "Finance & Purchase").first()
    adm = db.query(Department).filter(Department.name == "Administration").first()

    actions_data = [
        {"action_ref": "ACT/03/26/3327", "incident_id": 1, "description": "Install spill containment barriers", "ca_pa": "Preventive", "hierarchy_of_control": "Engineering Controls", "priority": "High", "owner_id": 952, "department_id": hse.id, "due_date": date.today() + timedelta(days=3), "status": "In-progress", "created_by_id": 104},
        {"action_ref": "ACT/03/26/3325", "incident_id": 1, "description": "Install spill containment systems", "ca_pa": "Corrective", "hierarchy_of_control": "Engineering Controls", "priority": "High", "owner_id": 445, "department_id": hse.id, "due_date": date.today() + timedelta(days=3), "status": "In-progress", "created_by_id": 104},
        {"action_ref": "ACT/03/26/3315", "incident_id": 2, "description": "Install protective barriers", "ca_pa": "Corrective", "hierarchy_of_control": "Engineering Controls", "priority": "Medium", "owner_id": 895, "department_id": hse.id, "due_date": date.today() - timedelta(days=3), "status": "Overdue", "created_by_id": 104},
        {"action_ref": "ACT/03/26/3273", "incident_id": 4, "description": "Conduct safety training", "ca_pa": "Corrective", "hierarchy_of_control": "Administrative Controls", "priority": "Medium", "owner_id": 703, "department_id": hse.id, "due_date": date.today() - timedelta(days=4), "status": "Overdue", "created_by_id": 104},
        {"action_ref": "ACT/03/26/3316", "incident_id": 2, "description": "Conduct periodic inspections", "ca_pa": "Preventive", "hierarchy_of_control": "Administrative Controls", "priority": "High", "owner_id": 3589, "department_id": fin.id, "due_date": date.today() - timedelta(days=5), "status": "Overdue", "created_by_id": 104},
    ]
    for ad in actions_data:
        db.add(Action(**ad))

    db.flush()
    print(f"  ✅ Seeded {len(incidents_data)} incidents, {len(rca_data)} RCA records, {len(actions_data)} actions")


if __name__ == "__main__":
    from database import SessionLocal
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
