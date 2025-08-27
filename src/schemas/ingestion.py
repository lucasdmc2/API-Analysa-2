"""
Pydantic schemas for ingestion endpoints
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import uuid

from src.schemas.common import BaseResponse, Artifact


class CreateIngestionRequest(BaseModel):
    """Request to create new ingestion"""
    document_type: str = Field(..., regex=r"^(laboratory_report|imaging_report)$")
    patient_id: Optional[uuid.UUID] = None
    upload_method: str = Field(default="direct", regex=r"^(direct|presigned_url)$")
    filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IngestionResponse(BaseResponse):
    """Response for ingestion creation"""
    ingestion_id: uuid.UUID
    status: str = Field(..., regex=r"^(created|uploading|processing|completed|failed)$")
    upload_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class IngestionProgress(BaseModel):
    """Processing progress information"""
    current_step: str = Field(..., regex=r"^(ocr|parsing|extraction|normalization|summary)$")
    progress_percent: int = Field(..., ge=0, le=100)


class IngestionStatus(BaseResponse):
    """Detailed ingestion status"""
    ingestion_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    status: str = Field(..., regex=r"^(uploaded|processing|completed|failed)$")
    pipeline_version: Optional[str] = None
    progress: Optional[IngestionProgress] = None
    error_message: Optional[str] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None