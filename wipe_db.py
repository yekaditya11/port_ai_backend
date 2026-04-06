from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS involved_persons, witnesses, equipment_involved, container_details, environmental_details, task_conditions, permit_details, actions, root_cause_analyses, workflow_events, incidents, enum_values, users, departments, sub_areas, operational_activities, equipment, shipping_lines CASCADE;"))
    print("Database tables dropped successfully. Restart the server to recreate them with the new schema.")
