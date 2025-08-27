"""
Reports API endpoints for retrieving processed clinical reports
"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas.clinical import ReportResponse
from src.services.reports import ReportsService
from src.services.auth import get_current_user, require_scope

router = APIRouter()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("read")),
):
    """Get structured clinical report with observations and summary"""
    
    reports_service = ReportsService(db, current_user.tenant_id)
    return await reports_service.get_report(report_id)