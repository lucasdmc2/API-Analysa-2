"""
Pydantic schemas for clinical data (patients, observations, reports)
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
import uuid

from src.schemas.common import BaseResponse, Organization, Period, Provenance, PaginationResponse


class Patient(BaseModel):
    """Patient demographics model"""
    patient_id: uuid.UUID
    external_id: Optional[str] = None
    age_years: Optional[int] = None
    sex: Optional[str] = Field(None, regex=r"^(male|female|other|unknown)$")
    pregnancy_status: Optional[str] = Field(None, regex=r"^(not_pregnant|pregnant|unknown|not_applicable)$")


class ReferenceRange(BaseModel):
    """Reference range model"""
    low: Optional[Decimal] = None
    high: Optional[Decimal] = None
    text: Optional[str] = None
    applies_to: Optional[dict] = None


class Observation(BaseResponse):
    """Lab test observation model"""
    observation_id: uuid.UUID
    loinc_code: Optional[str] = Field(None, regex=r"^[0-9]+-[0-9]$")
    display: str
    analyte_raw: Optional[str] = None
    value_numeric: Optional[Decimal] = None
    value_text: Optional[str] = None
    unit_ucum: Optional[str] = None
    unit_raw: Optional[str] = None
    reference_range: Optional[ReferenceRange] = None
    flag: Optional[str] = Field(None, regex=r"^(L|N|H|LL|HH)$")
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)
    method_name: Optional[str] = None
    sample_type: Optional[str] = None
    collected_at: Optional[datetime] = None
    resulted_at: Optional[datetime] = None


class Recommendation(BaseModel):
    """Clinical recommendation model"""
    code: str
    text: str
    level: str = Field(..., regex=r"^(info|attention|urgent)$")
    evidence: Optional[str] = None
    disclaimer: str = "Esta recomendação é informativa e não substitui avaliação médica."


class ReportResponse(BaseResponse):
    """Structured clinical report response"""
    report_id: uuid.UUID
    patient: Patient
    category: str = Field(..., regex=r"^(laboratory|imaging)$")
    title: Optional[str] = None
    conclusion_text: Optional[str] = None
    summary_pt: Optional[str] = None
    recommendations: List[Recommendation] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    status: str = Field(..., regex=r"^(preliminary|final|corrected)$")
    issued_at: Optional[datetime] = None
    effective_period: Optional[Period] = None
    performer_organization: Optional[Organization] = None
    provenance: Optional[Provenance] = None
    created_at: datetime


class ObservationList(BaseResponse):
    """Paginated list of observations"""
    data: List[Observation]
    pagination: PaginationResponse