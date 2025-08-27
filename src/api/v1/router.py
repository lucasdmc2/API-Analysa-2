"""
Main API router for v1 endpoints
"""

from fastapi import APIRouter

from src.api.v1 import ingestion, reports, patients, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(ingestion.router, prefix="/ingestions", tags=["Ingestão"])
api_router.include_router(reports.router, prefix="/reports", tags=["Laudos"])
api_router.include_router(patients.router, prefix="/patients", tags=["Pacientes"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administração"])