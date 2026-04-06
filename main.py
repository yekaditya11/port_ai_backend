from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import engine, SessionLocal, Base

# Import all models so they register with Base.metadata
import models  # noqa: F401

from routers import enums, incidents, rca, actions, workflow, dashboard
from seeds.seed_data import seed_all

settings = get_settings()

app = FastAPI(
    title="QavachAI - Incident Management API",
    description="Backend API for the QavachAI Incident Management Dashboard",
    version="1.0.0",
)

# CORS — allow frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(enums.router)
app.include_router(incidents.router)
app.include_router(rca.router)
app.include_router(actions.router)
app.include_router(workflow.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    """Create all tables and seed data on first run."""
    print("🚀 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")

    # Auto-seed
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "QavachAI Incident Management API", "status": "running", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
