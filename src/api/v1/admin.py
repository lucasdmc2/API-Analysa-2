"""
Administration API endpoints for configuration and management
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas.reference import (
    CreateRangesetRequest, RangesetResponse, RangesetList,
    CreateLoincMappingRequest, LoincMappingResponse, LoincMappingList
)
from src.services.admin import AdminService
from src.services.auth import get_current_user, require_scope

router = APIRouter()


@router.post("/rangesets", response_model=RangesetResponse, status_code=201)
async def create_rangeset(
    request: CreateRangesetRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("admin")),
):
    """Create new reference range configuration"""
    
    admin_service = AdminService(db, current_user.tenant_id)
    return await admin_service.create_rangeset(request)


@router.get("/rangesets", response_model=RangesetList)
async def list_rangesets(
    analyte_key: Optional[str] = Query(None),
    loinc_code: Optional[str] = Query(None),
    lab_org_id: Optional[uuid.UUID] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("read")),
):
    """List reference ranges with filtering"""
    
    admin_service = AdminService(db, current_user.tenant_id)
    return await admin_service.list_rangesets(
        analyte_key=analyte_key,
        loinc_code=loinc_code,
        lab_org_id=lab_org_id,
        cursor=cursor,
        limit=limit,
    )


@router.post("/mappings/loinc", response_model=LoincMappingResponse, status_code=201)
async def create_loinc_mapping(
    request: CreateLoincMappingRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("admin")),
):
    """Create or update LOINC mapping"""
    
    admin_service = AdminService(db, current_user.tenant_id)
    return await admin_service.create_loinc_mapping(request)


@router.get("/mappings/loinc", response_model=LoincMappingList)
async def list_loinc_mappings(
    lab_code: Optional[str] = Query(None),
    loinc_code: Optional[str] = Query(None),
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("read")),
):
    """List LOINC mappings"""
    
    admin_service = AdminService(db, current_user.tenant_id)
    return await admin_service.list_loinc_mappings(
        lab_code=lab_code,
        loinc_code=loinc_code,
        cursor=cursor,
        limit=limit,
    )