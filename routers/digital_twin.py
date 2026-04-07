from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.incident import Incident
from sqlalchemy import or_
from datetime import datetime

router = APIRouter(prefix="/api/digital-twin", tags=["Digital Twin"])

# 2D Coordinate Mapping for the Port Layout (W=700, H=480)
# Waterfront/Berths on the Left (x: 40-180)
# Operations/Yards in the Center (x: 220-400)
# Inland/Admin/Gates on the Right (x: 420-650)
ZONE_COORDINATES = {
    # Berths (Seaside - Left)
    "Container Berth": {"x": 60, "y": 140, "w": 120, "h": 60},
    "General Cargo Berth": {"x": 60, "y": 220, "w": 120, "h": 60},
    "Passenger Berth": {"x": 60, "y": 300, "w": 120, "h": 60},
    "Port Dock No. 3": {"x": 60, "y": 380, "w": 120, "h": 60},
    "Container & General Cargo Berth": {"x": 60, "y": 60, "w": 120, "h": 60},
    "Dockside Operations": {"x": 140, "y": 140, "w": 40, "h": 300},

    # Yards & Operations (Center)
    "Container Yard": {"x": 220, "y": 140, "w": 160, "h": 120},
    "Container Terminal B": {"x": 220, "y": 280, "w": 160, "h": 100},
    "CFS Yard": {"x": 220, "y": 60, "w": 160, "h": 60},
    "IMDG Yard": {"x": 420, "y": 140, "w": 100, "h": 80},  # Hazmat
    "Hazardous Spill Bund Area": {"x": 420, "y": 60, "w": 100, "h": 60},
    "RORO yard": {"x": 220, "y": 400, "w": 160, "h": 60},
    "Container Parking Yard": {"x": 420, "y": 240, "w": 100, "h": 60},
    "ITV Parking area": {"x": 420, "y": 320, "w": 100, "h": 40},

    # Storage & Facilities (Right-Center)
    "Warehouse": {"x": 540, "y": 140, "w": 120, "h": 80},
    "Dry cargo Warehouse": {"x": 540, "y": 240, "w": 120, "h": 60},
    "Storage Tank Farm": {"x": 540, "y": 60, "w": 120, "h": 60},
    "Tank farm": {"x": 540, "y": 320, "w": 120, "h": 60},
    "Chemical Storage Area": {"x": 420, "y": 380, "w": 100, "h": 80},
    "Bunkering Station": {"x": 540, "y": 400, "w": 120, "h": 60},

    # Admin & Utils (Right)
    "Admin. Building": {"x": 680, "y": 60, "w": 80, "h": 100},
    "Security Main Gate": {"x": 680, "y": 200, "w": 80, "h": 60},
    "Gate": {"x": 680, "y": 280, "w": 80, "h": 60},
    "Occupational Health Center": {"x": 680, "y": 360, "w": 80, "h": 60},
    "Engineering Workshop": {"x": 680, "y": 440, "w": 80, "h": 40},
    "Social Facility": {"x": 780, "y": 60, "w": 60, "h": 60},
    "Pumphouse": {"x": 780, "y": 140, "w": 60, "h": 60},
    "Substation": {"x": 780, "y": 220, "w": 60, "h": 60},
    "Waste Reception Facility": {"x": 780, "y": 300, "w": 60, "h": 60},
    "Bilge Facility": {"x": 780, "y": 380, "w": 60, "h": 60},
    "Fuel station": {"x": 540, "y": 480, "w": 120, "h": 40},
}

DEFAULT_COORDS = {"x": 350, "y": 240, "w": 50, "h": 50}

@router.get("/live")
def get_live_twin_data(db: Session = Depends(get_db)):
    """Fetches real incidents and combines with mock live data for the digital twin."""
    
    # 1. Fetch active incidents (not Closed)
    active_incidents = db.query(Incident).filter(
        Incident.status != "Closed"
    ).order_by(Incident.created_at.desc()).all()

    incidents_payload = []
    for inc in active_incidents:
        area = inc.area_of_incident or "Entire Terminal"
        coords = ZONE_COORDINATES.get(area, DEFAULT_COORDS)
        
        # Determine incident type icon/vibe
        inc_type = "equipment_failure"
        if inc.incident_type and len(inc.incident_type) > 0:
            primary_type = inc.incident_type[0].lower()
            if "fire" in primary_type: inc_type = "fire"
            elif "spill" in primary_type: inc_type = "spill"
            elif "injury" in primary_type or "medical" in primary_type: inc_type = "worker_injury"
            elif "gas" in primary_type or "leak" in primary_type: inc_type = "gas_leak"

        incidents_payload.append({
            "id": str(inc.id),
            "type": inc_type,
            "severity": (inc.actual_severity or "medium").lower(),
            "zone": area,
            "x": coords["x"] + (coords["w"] // 2),
            "y": coords["y"] + (coords["h"] // 2),
            "time": inc.reported_date.strftime("%H:%M") if inc.reported_date else inc.created_at.strftime("%H:%M"),
            "status": "active" if inc.status == "New" else "responding",
            "description": inc.incident_title or inc.description or "No Title"
        })

    # 2. Mock Vessels
    vessels = [
        {"id": "v1", "name": "MSC AURORA", "type": "container", "x": 40, "y": 140, "rotation": 0, "status": "docked", "cargo": "Electronics", "flag": "PA"},
        {"id": "v2", "name": "PACIFIC STAR", "type": "tanker", "x": 40, "y": 220, "rotation": 0, "status": "docked", "cargo": "Crude Oil", "flag": "LR"},
        {"id": "v3", "name": "TITAN BULK", "type": "bulk", "x": 40, "y": 300, "rotation": 0, "status": "docked", "cargo": "Grain", "flag": "MH"},
        {"id": "v4", "name": "HORIZON QUEEN", "type": "container", "x": -100, "y": 185, "rotation": 12, "status": "approaching", "cargo": "Machinery", "flag": "SG", "eta": "14:32"},
    ]

    # 3. Mock Activities (Combining real incidents with some mock noise)
    activities = []
    for inc in active_incidents[:5]:
        activities.append({
            "id": f"act_real_{inc.id}",
            "message": f"Incident reported: {inc.incident_title or inc.area_of_incident}",
            "type": "critical" if inc.actual_severity == "High" else "warning",
            "time": inc.created_at.strftime("%H:%M")
        })
    
    # Add some mock ones if empty or to fill up
    activities.extend([
        {"id": "a_m1", "message": "TITAN BULK — mooring complete, crane ops starting", "type": "info", "time": "10:18"},
        {"id": "a_m2", "message": "Gate shift change completed — 4 officers on duty", "type": "info", "time": "10:14"},
        {"id": "a_m3", "message": "AIS: HORIZON QUEEN ETA updated to 14:32", "type": "info", "time": "10:12"},
    ])

    return {
        "incidents": incidents_payload,
        "vessels": vessels,
        "activities": activities[:10],
        "zones": [
            {"id": k, "name": k, "x": v["x"], "y": v["y"], "w": v["w"], "h": v["h"], "risk": "safe"} 
            for k, v in ZONE_COORDINATES.items()
        ]
    }
