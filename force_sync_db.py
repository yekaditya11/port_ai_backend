from database import engine, Base, SessionLocal
import models
from seeds.seed_data import seed_all
from sqlalchemy import text

print("🧹 Dropping all tables...")
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS involved_persons, witnesses, equipment_involved, container_details, environmental_details, task_conditions, permit_details, actions, root_cause_analyses, workflow_events, incidents, enum_values, users, departments, sub_areas, operational_activities, equipment, shipping_lines CASCADE;"))

print("🏗️ Creating all tables...")
Base.metadata.create_all(bind=engine)

print("🌱 Seeding database...")
db = SessionLocal()
try:
    seed_all(db)
    print("✅ Sync complete!")
finally:
    db.close()
