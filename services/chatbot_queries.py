from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _date_bounds(params: dict[str, Any]):
    today = date.today()
    date_range = params.get("date_range") or "all"

    if date_range == "today":
        from_date = today
        to_date = today
    elif date_range == "yesterday":
        from_date = today - timedelta(days=1)
        to_date = from_date
    elif date_range == "last_7_days":
        from_date = today - timedelta(days=7)
        to_date = today
    elif date_range == "last_30_days":
        from_date = today - timedelta(days=30)
        to_date = today
    elif date_range == "this_month":
        from_date = today.replace(day=1)
        to_date = today
    elif date_range == "custom":
        from_date = _parse_date(params.get("from_date"))
        to_date = _parse_date(params.get("to_date"))
    else:
        from_date = None
        to_date = None

    sql_params = {}
    clauses = []
    if from_date:
        sql_params["from_date"] = datetime.combine(from_date, time.min)
        clauses.append("{date_column} >= :from_date")
    if to_date:
        sql_params["to_date"] = datetime.combine(to_date, time.max)
        clauses.append("{date_column} <= :to_date")

    return clauses, sql_params


def _where_clause(date_column: str, params: dict[str, Any]):
    clauses, sql_params = _date_bounds(params)
    if not clauses:
        return "", sql_params
    return "WHERE " + " AND ".join(
        clause.format(date_column=date_column) for clause in clauses
    ), sql_params


def _rows_to_table(rows) -> dict[str, Any]:
    rows = list(rows)
    if not rows:
        return {"columns": [], "rows": []}

    columns = list(rows[0]._mapping.keys())
    table_rows = [
        [
            value.isoformat() if isinstance(value, (datetime, date)) else value
            for value in row._mapping.values()
        ]
        for row in rows
    ]
    return {"columns": columns, "rows": table_rows}


def _execute(db: Session, sql: str, params: dict[str, Any]):
    rows = db.execute(text(sql), params).fetchall()
    return _rows_to_table(rows)


def _count_answer(label: str, table: dict[str, Any]) -> str:
    if not table["rows"]:
        return f"No {label} were found."
    return f"{label.capitalize()}: {table['rows'][0][0]}"


def _table_summary(label: str, table: dict[str, Any]) -> str:
    count = len(table["rows"])
    if count == 0:
        return f"No {label} found for the selected request."
    return f"Found {count} {label}."


def execute_chatbot_query(db: Session, plan: dict[str, Any]) -> dict[str, Any]:
    query_id = plan["query_id"]
    params = plan.get("params", {})
    limit = params.get("limit", 10)

    if query_id == "unknown":
        return {
            "answer": "I can answer common incident and observation questions, but I could not map this request to a supported query yet.",
            "table": None,
            "sql": None,
            "sources": [],
        }

    if query_id == "incident_count":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT COUNT(*) AS total FROM public.incidents {where}"
        table = _execute(db, sql, sql_params)
        return {"answer": _count_answer("incidents", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "observation_count":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT COUNT(*) AS total FROM public.observations {where}"
        table = _execute(db, sql, sql_params)
        return {"answer": _count_answer("observations", table), "table": table, "sql": sql, "sources": ["observations"]}

    if query_id == "safety_event_count":
        incident_where, incident_params = _where_clause("reported_date", params)
        observation_where, observation_params = _where_clause("reported_date", params)
        sql = f"""
        SELECT 'incidents' AS source, COUNT(*) AS total
        FROM public.incidents
        {incident_where}
        UNION ALL
        SELECT 'observations' AS source, COUNT(*) AS total
        FROM public.observations
        {observation_where}
        """
        table = _execute(db, sql, {**incident_params, **observation_params})
        total = sum(row[1] for row in table["rows"])
        return {"answer": f"Total safety events: {total}", "table": table, "sql": sql, "sources": ["incidents", "observations"]}

    if query_id == "latest_incidents":
        sql = """
        SELECT incident_ref, status, reported_date, area_of_incident, operational_activity, incident_title
        FROM public.incidents
        ORDER BY COALESCE(reported_date, created_at) DESC NULLS LAST
        LIMIT :limit
        """
        table = _execute(db, sql, {"limit": limit})
        return {"answer": _table_summary("incidents", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "latest_observations":
        sql = """
        SELECT observation_ref, status, reported_date, area_of_observation, operational_activity, observation_group
        FROM public.observations
        ORDER BY reported_date DESC
        LIMIT :limit
        """
        table = _execute(db, sql, {"limit": limit})
        return {"answer": _table_summary("observations", table), "table": table, "sql": sql, "sources": ["observations"]}

    if query_id == "latest_safety_events":
        sql = """
        SELECT 'incident' AS source, incident_ref AS ref, status, reported_date, area_of_incident AS area, operational_activity
        FROM public.incidents
        UNION ALL
        SELECT 'observation' AS source, observation_ref AS ref, status, reported_date, area_of_observation AS area, operational_activity
        FROM public.observations
        ORDER BY reported_date DESC NULLS LAST
        LIMIT :limit
        """
        table = _execute(db, sql, {"limit": limit})
        return {"answer": _table_summary("safety events", table), "table": table, "sql": sql, "sources": ["incidents", "observations"]}

    if query_id == "incident_by_status":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT status, COUNT(*) AS total FROM public.incidents {where} GROUP BY status ORDER BY total DESC, status ASC"
        table = _execute(db, sql, sql_params)
        return {"answer": _table_summary("incident status groups", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "observation_by_status":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT status, COUNT(*) AS total FROM public.observations {where} GROUP BY status ORDER BY total DESC, status ASC"
        table = _execute(db, sql, sql_params)
        return {"answer": _table_summary("observation status groups", table), "table": table, "sql": sql, "sources": ["observations"]}

    if query_id == "incident_by_area":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT area_of_incident, COUNT(*) AS total FROM public.incidents {where} GROUP BY area_of_incident ORDER BY total DESC, area_of_incident ASC LIMIT :limit"
        table = _execute(db, sql, {**sql_params, "limit": limit})
        return {"answer": _table_summary("incident area groups", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "observation_by_area":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT area_of_observation, COUNT(*) AS total FROM public.observations {where} GROUP BY area_of_observation ORDER BY total DESC, area_of_observation ASC LIMIT :limit"
        table = _execute(db, sql, {**sql_params, "limit": limit})
        return {"answer": _table_summary("observation area groups", table), "table": table, "sql": sql, "sources": ["observations"]}

    if query_id == "incident_by_activity":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT operational_activity, COUNT(*) AS total FROM public.incidents {where} GROUP BY operational_activity ORDER BY total DESC, operational_activity ASC LIMIT :limit"
        table = _execute(db, sql, {**sql_params, "limit": limit})
        return {"answer": _table_summary("incident activity groups", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "observation_by_activity":
        where, sql_params = _where_clause("reported_date", params)
        sql = f"SELECT operational_activity, COUNT(*) AS total FROM public.observations {where} GROUP BY operational_activity ORDER BY total DESC, operational_activity ASC LIMIT :limit"
        table = _execute(db, sql, {**sql_params, "limit": limit})
        return {"answer": _table_summary("observation activity groups", table), "table": table, "sql": sql, "sources": ["observations"]}

    if query_id == "observation_near_miss_count":
        where, sql_params = _where_clause("reported_date", params)
        near_miss_filter = f"{where} {'AND' if where else 'WHERE'} near_miss IS TRUE"
        count_sql = f"SELECT COUNT(*) AS total FROM public.observations {near_miss_filter}"
        count_table = _execute(db, count_sql, sql_params)
        total = count_table["rows"][0][0] if count_table["rows"] else 0

        sample_sql = f"""
        SELECT observation_ref, status, reported_date, area_of_observation, operational_activity, observation_group
        FROM public.observations
        {near_miss_filter}
        ORDER BY reported_date DESC
        LIMIT :limit
        """
        table = _execute(db, sample_sql, {**sql_params, "limit": 5})
        return {
            "answer": f"Near miss observations: {total}. Showing the latest {len(table['rows'])} records.",
            "table": table,
            "sql": f"{count_sql}; {sample_sql}",
            "sources": ["observations"],
            "metadata": {"total": total, "preview_limit": 5},
        }

    if query_id == "incident_detail":
        sql = """
        SELECT incident_ref, status, reported_date, incident_date, area_of_incident, operational_activity, incident_title, description, immediate_action
        FROM public.incidents
        WHERE incident_ref = :reference
        LIMIT 1
        """
        table = _execute(db, sql, {"reference": params.get("reference")})
        return {"answer": _table_summary("incident records", table), "table": table, "sql": sql, "sources": ["incidents"]}

    if query_id == "observation_detail":
        sql = """
        SELECT observation_ref, status, reported_date, area_of_observation, department, operational_activity, observation_group, description, immediate_action
        FROM public.observations
        WHERE observation_ref = :reference
        LIMIT 1
        """
        table = _execute(db, sql, {"reference": params.get("reference")})
        return {"answer": _table_summary("observation records", table), "table": table, "sql": sql, "sources": ["observations"]}

    return {
        "answer": "This query template is not implemented yet.",
        "table": None,
        "sql": None,
        "sources": [],
    }
