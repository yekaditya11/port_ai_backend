from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE incidents, root_cause_analyses, actions, workflow_events, enum_values, departments, users, sub_areas, operational_activities, equipment, shipping_lines RESTART IDENTITY CASCADE;"))
    print("Database wiped successfully.")
