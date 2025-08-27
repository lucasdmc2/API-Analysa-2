"""
Patients API endpoints for patient data and observations
"""

import uuid
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas.clinical import ObservationList
from src.services.patients import PatientsService
from src.services.auth import get_current_user, require_scope

router = APIRouter()


@router.get("/{patient_id}/observations", response_model=ObservationList)
async def get_patient_observations(
    patient_id: uuid.UUID,
    loinc_code: Optional[str] = Query(None, regex=r"^[0-9]+-[0-9]$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    flag: Optional[str] = Query(None, regex=r"^(L|N|H|LL|HH)$"),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("read")),
):
    """List patient's lab observations with filtering and pagination"""
    
    patients_service = PatientsService(db, current_user.tenant_id)
    return await patients_service.get_patient_observations(
        patient_id=patient_id,
        loinc_code=loinc_code,
        date_from=date_from,
        date_to=date_to,
        flag=flag,
        cursor=cursor,
        limit=limit,
    )