from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from database import get_db
from models.incident import Incident
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    days: int = 30, 
    start_date: str = Query(None), 
    end_date: str = Query(None), 
    db: Session = Depends(get_db)
):
    """Aggregated stats for the Dashboard page — stat cards, charts, tables."""
    now = datetime.utcnow()
    
    if start_date and end_date:
        try:
            # Handle potential ISO format differences
            cutoff_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            cutoff_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            duration_days = (cutoff_end - cutoff_start).days or 1
        except ValueError:
            cutoff_start = now - timedelta(days=days)
            cutoff_end = now
            duration_days = days
    else:
        cutoff_start = now - timedelta(days=days)
        cutoff_end = now
        duration_days = days

    cutoff_90 = now - timedelta(days=90) # Still useful for some table comparisons

    # --- Stat Cards ---
    total_incidents = db.query(func.count(Incident.id)).filter(
        Incident.created_at >= cutoff_start, 
        Incident.created_at <= cutoff_end
    ).scalar() or 0
    
    open_incidents = db.query(func.count(Incident.id)).filter(
        Incident.status.notin_(["Closed", "Resolution"])
    ).scalar() or 0

    # Distinct days with incidents in custom range
    incident_days = db.query(func.count(func.distinct(func.date(Incident.incident_date)))).filter(
        Incident.incident_date >= cutoff_start,
        Incident.incident_date <= cutoff_end
    ).scalar() or 0

    incident_free_days = max(0, duration_days - incident_days)

    # Days since last injury (Global, regardless of range)
    last_injury = db.query(func.max(Incident.incident_date)).filter(
        Incident.incident_type.contains(["Injury & Ill Health"])
    ).scalar()
    injury_free_days = (now - last_injury).days if last_injury else "--"

    stat_cards = {
        "incidents_last_30_days": total_incidents,
        "incident_days": incident_days,
        "open_incidents": open_incidents,
        "incident_free_days": incident_free_days,
        "injury_free_days": injury_free_days,
        "days_since_fatality": "--"
    }

    # --- By Incident Type (Pie Chart) ---
    all_types = db.query(Incident.incident_type).filter(
        Incident.incident_type.isnot(None),
        Incident.created_at >= cutoff_start,
        Incident.created_at <= cutoff_end
    ).all()
    type_counts = {}
    for (t_list,) in all_types:
        if isinstance(t_list, list):
            for t in t_list:
                type_counts[t] = type_counts.get(t, 0) + 1
        elif t_list:
            type_counts[t_list] = type_counts.get(t_list, 0) + 1
    
    by_incident_type = [{"name": t, "value": c} for t, c in type_counts.items()]

    # --- By Work Area (List) ---
    area_rows = db.query(
        Incident.area_of_incident, func.count(Incident.id)
    ).filter(
        Incident.area_of_incident.isnot(None),
        Incident.created_at >= cutoff_start,
        Incident.created_at <= cutoff_end
    ).group_by(Incident.area_of_incident).order_by(func.count(Incident.id).desc()).limit(6).all()

    by_work_area = [{"name": a, "count": c} for a, c in area_rows]

    # --- By Status (Bar Chart) ---
    status_rows = db.query(
        Incident.status, func.count(Incident.id)
    ).filter(
        Incident.created_at >= cutoff_start,
        Incident.created_at <= cutoff_end
    ).group_by(Incident.status).all()

    all_statuses = ["New", "Review", "Investigation", "Overdue", "Reopened", "Resolved", "Rejected", "Inspection"]
    status_map = {s: c for s, c in status_rows}
    by_status = [{"name": s, "value": status_map.get(s, 0)} for s in all_statuses]

    # --- Overview Table ---
    overview_types = [
        ("Fatality", "5-Catastrophic"),
        ("Serious Injury", "4-Major"),
        ("Lost Time Injury", "3-Moderate"),
        ("Environment", None),
        ("Asset Damage", None),
    ]
    overview_table = []
    for label, severity in overview_types:
        if severity:
            q_current = db.query(func.count(Incident.id)).filter(
                Incident.actual_severity == severity, 
                Incident.created_at >= cutoff_start,
                Incident.created_at <= cutoff_end
            ).scalar() or 0
            # For comparison logic, we still use a default 90-day window or similar
            q90 = db.query(func.count(Incident.id)).filter(
                Incident.actual_severity == severity, Incident.created_at >= cutoff_90
            ).scalar() or 0
        else:
            q_current = db.query(func.count(Incident.id)).filter(
                Incident.incident_type.contains([label]), 
                Incident.created_at >= cutoff_start,
                Incident.created_at <= cutoff_end
            ).scalar() or 0
            q90 = db.query(func.count(Incident.id)).filter(
                Incident.incident_type.contains([label]), Incident.created_at >= cutoff_90
            ).scalar() or 0

        overview_table.append({
            "type": label,
            "last_30": q_current,
            "var_30": f"100%({q_current})" if q_current > 0 else "0(0)",
            "last_90": q90,
            "var_90": f"100%({q90})" if q90 > 0 else "0(0)",
        })

    # --- Accidents Timeline ---
    accidents_timeline = []
    # Dynamic buckets based on duration
    bucket_size = max(1, duration_days // 6)
    for bucket_start_day in range(0, duration_days, bucket_size):
        b_start = cutoff_start + timedelta(days=bucket_start_day)
        b_end = min(cutoff_end, b_start + timedelta(days=bucket_size))
        count = db.query(func.count(Incident.id)).filter(
            Incident.incident_date >= b_start, Incident.incident_date < b_end
        ).scalar() or 0
        accidents_timeline.append({"day_bucket": f"{bucket_start_day} Days", "count": count})

    return {
        "stat_cards": stat_cards,
        "by_incident_type": by_incident_type,
        "by_work_area": by_work_area,
        "by_status": by_status,
        "overview_table": overview_table,
        "accidents_timeline": accidents_timeline,
    }


@router.get("/trend")
def get_trend_stats(days: int = 30, db: Session = Depends(get_db)):
    """Detailed trend analytics for the Trend Dashboard page."""
    now = datetime.utcnow()
    cutoff_trend = now - timedelta(days=90)  # Larger window for trends

    # 1. Severity Distribution (Pie)
    severity_rows = db.query(
        Incident.actual_severity, func.count(Incident.id)
    ).filter(Incident.actual_severity.isnot(None), Incident.actual_severity != "Select").group_by(Incident.actual_severity).all()
    
    # Map colors for the frontend
    colors = {
        "1-Negligible": "#78d2c0",
        "2-Minor": "#a4ce7e",
        "3-Moderate": "#f2a654",
        "4-Major": "#4cb4e7",
        "5-Catastrophic": "#f46a6a"
    }
    severity_data = [{"name": s, "value": c, "color": colors.get(s, "#94a3b8")} for s, c in severity_rows]

    # 2. Root Cause Distribution (Bar) - Using Incident Group as the primary proxy
    # We fetch all groups and count in Python for maximum robustness
    all_groups = db.query(Incident.incident_group).filter(Incident.incident_group.isnot(None)).all()
    group_counts = {}
    for (g_list,) in all_groups:
        if isinstance(g_list, list):
            for g in g_list:
                group_counts[g] = group_counts.get(g, 0) + 1
        elif g_list:
            group_counts[g_list] = group_counts.get(g_list, 0) + 1
    
    root_cause_data = [{"name": g[:10] + ".." if len(g) > 10 else g, "value": c} for g, c in group_counts.items()]

    # 3. Weekly Trend (Line) - Last 12 weeks
    trend_data = []
    for week in range(12, 0, -1):
        start = now - timedelta(days=week * 7)
        end = now - timedelta(days=(week - 1) * 7)
        count = db.query(func.count(Incident.id)).filter(
            Incident.incident_date >= start, Incident.incident_date < end
        ).scalar() or 0
        trend_data.append({"name": str(13 - week), "value": count})

    # 4. Top 5 Incidents
    top_incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(5).all()
    
    # 5. Specialized Stat Grid
    total_90 = db.query(func.count(Incident.id)).filter(Incident.created_at >= cutoff_trend).scalar() or 0
    total_prev_90 = db.query(func.count(Incident.id)).filter(
        and_(Incident.created_at >= (now - timedelta(days=180)), Incident.created_at < cutoff_trend)
    ).scalar() or 0
    
    trend_stats = {
        "total_incidents": total_90,
        "prev_total": total_prev_90,
        "lti_count": db.query(func.count(Incident.id)).filter(Incident.actual_severity == "3-Moderate").scalar() or 0,
        "med_count": db.query(func.count(Incident.id)).filter(Incident.actual_severity == "2-Minor").scalar() or 0,
    }

    return {
        "severity_data": severity_data,
        "root_cause_data": root_cause_data,
        "trend_data": trend_data,
        "top_incidents": [
            {
                "id": i.id,
                "ref": i.incident_ref,
                "title": i.incident_title,
                "date": i.incident_date.strftime("%d %b %y") if i.incident_date else "--",
                "severity": i.actual_severity
            } for i in top_incidents
        ],
        "stats": trend_stats
    }
