"""
Common Pydantic schemas shared across the API
"""

from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class PaginationResponse(BaseModel):
    """Standard pagination response"""
    next_cursor: Optional[str] = None
    has_next: bool
    limit: int
    total_count: Optional[int] = None


class Period(BaseModel):
    """Time period model"""
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class Organization(BaseModel):
    """Organization model"""
    organization_id: uuid.UUID
    name: str
    identifier: Optional[str] = None
    org_type: str = Field(..., regex=r"^(laboratory|hospital|clinic|other)$")


class Artifact(BaseModel):
    """Processing artifact model"""
    type: str = Field(..., regex=r"^(original_document|ocr_result|parsed_data|normalized_data)$")
    uri: str
    size_bytes: Optional[int] = None
    created_at: datetime


class Provenance(BaseModel):
    """Data provenance model"""
    pipeline_version: str
    config_hash: str
    document_sha256: str
    artifacts: list[Artifact] = []
    processing_time_ms: Optional[int] = None


class BaseResponse(BaseModel):
    """Base response model with metadata"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v),
        }