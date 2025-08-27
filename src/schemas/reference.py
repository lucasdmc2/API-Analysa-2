"""
Pydantic schemas for reference data (ranges, mappings, organizations)
"""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import uuid

from src.schemas.common import BaseResponse, Organization, PaginationResponse


class CreateRangesetRequest(BaseModel):
    """Request to create reference range"""
    analyte_key: str
    loinc_code: Optional[str] = Field(None, regex=r"^[0-9]+-[0-9]$")
    lab_org_id: Optional[uuid.UUID] = None
    age_min_years: Optional[int] = Field(None, ge=0)
    age_max_years: Optional[int] = Field(None, ge=0)
    sex: str = Field(default="all", regex=r"^(male|female|all)$")
    pregnancy_status: str = Field(default="all", regex=r"^(pregnant|not_pregnant|all)$")
    method_name: Optional[str] = None
    ref_low: Optional[Decimal] = None
    ref_high: Optional[Decimal] = None
    ref_text: Optional[str] = None
    unit_ucum: str
    source: Optional[str] = None
    confidence_level: str = Field(default="medium", regex=r"^(low|medium|high)$")

    @validator("age_max_years")
    def validate_age_range(cls, v, values):
        if v is not None and values.get("age_min_years") is not None:
            if v < values["age_min_years"]:
                raise ValueError("age_max_years must be >= age_min_years")
        return v


class RangesetAppliesTo(BaseModel):
    """Range applicability criteria"""
    age_min_years: Optional[int] = None
    age_max_years: Optional[int] = None
    sex: Optional[str] = None
    pregnancy_status: Optional[str] = None
    method_name: Optional[str] = None


class RangesetResponse(BaseResponse):
    """Reference range response"""
    rangeset_id: uuid.UUID
    analyte_key: str
    loinc_code: Optional[str] = None
    lab_organization: Optional[Organization] = None
    applies_to: RangesetAppliesTo
    ref_low: Optional[Decimal] = None
    ref_high: Optional[Decimal] = None
    ref_text: Optional[str] = None
    unit_ucum: str
    source: Optional[str] = None
    confidence_level: str
    effective_period: Optional[dict] = None
    created_at: datetime


class RangesetList(BaseResponse):
    """Paginated list of reference ranges"""
    data: List[RangesetResponse]
    pagination: PaginationResponse


class CreateLoincMappingRequest(BaseModel):
    """Request to create LOINC mapping"""
    lab_code: str
    lab_name: str
    loinc_code: str = Field(..., regex=r"^[0-9]+-[0-9]$")
    loinc_display: str
    confidence: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    method_constraint: Optional[str] = None
    unit_constraint: Optional[str] = None


class LoincMappingResponse(BaseResponse):
    """LOINC mapping response"""
    mapping_id: uuid.UUID
    lab_code: str
    lab_name: str
    loinc_code: str
    loinc_display: str
    confidence: Decimal
    method_constraint: Optional[str] = None
    unit_constraint: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None


class LoincMappingList(BaseResponse):
    """Paginated list of LOINC mappings"""
    data: List[LoincMappingResponse]
    pagination: PaginationResponse