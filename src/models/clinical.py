"""
SQLAlchemy models for clinical data (patients, lab tests, reports)
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Numeric, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.db.database import Base


class Patient(Base):
    """Patient model with demographics"""
    __tablename__ = "patient"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    external_id = Column(String(100), index=True)
    name_encrypted = Column(Text)  # PII encrypted
    date_of_birth = Column(Date)
    sex = Column(String(10))  # male, female, other, unknown
    pregnancy_status = Column(String(20))  # not_pregnant, pregnant, unknown, not_applicable
    weight_kg = Column(Numeric(5, 2))
    height_cm = Column(Numeric(5, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default={})
    
    # Relationships
    lab_tests = relationship("LabTest", back_populates="patient")
    reports = relationship("Report", back_populates="patient")


class LabTest(Base):
    """Lab test observation model with LOINC normalization"""
    __tablename__ = "lab_test"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=False, index=True)
    extraction_job_id = Column(UUID(as_uuid=True), ForeignKey("extraction_job.id"), nullable=False)
    
    # LOINC normalization
    loinc_code = Column(String(10), index=True)  # e.g., "2345-7"
    analyte_display = Column(Text, nullable=False, index=True)
    analyte_raw = Column(Text)  # Original text from document
    
    # Values
    value_num = Column(Numeric(20, 6))  # Numeric value
    value_text = Column(Text)  # Text value for qualitative results
    unit_ucum = Column(String(50))  # UCUM normalized unit
    unit_raw = Column(Text)  # Original unit from document
    
    # Reference ranges
    ref_low = Column(Numeric(20, 6))
    ref_high = Column(Numeric(20, 6))
    ref_text = Column(Text)  # Textual reference (e.g., "negative")
    
    # Flags and metadata
    flag = Column(String(5))  # L, N, H, LL, HH
    confidence_score = Column(Numeric(3, 2))  # 0.00-1.00
    method_name = Column(Text)
    sample_type = Column(String(100))  # serum, plasma, urine, etc
    
    # Timestamps
    collected_at = Column(DateTime(timezone=True), index=True)
    resulted_at = Column(DateTime(timezone=True))
    reported_at = Column(DateTime(timezone=True))
    
    # Organization
    performer_org_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_json = Column(JSON)  # Full extraction details
    
    # Relationships
    patient = relationship("Patient", back_populates="lab_tests")
    document = relationship("Document", back_populates="lab_tests")
    extraction_job = relationship("ExtractionJob", back_populates="lab_tests")
    performer_organization = relationship("Organization")


class Report(Base):
    """Diagnostic report model with summary"""
    __tablename__ = "report"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=False, index=True)
    extraction_job_id = Column(UUID(as_uuid=True), ForeignKey("extraction_job.id"), nullable=False)
    
    category = Column(String(20), nullable=False, default="laboratory")  # laboratory, imaging
    code = Column(String(50))  # LOINC code for report type
    title = Column(Text)
    conclusion_text = Column(Text)
    summary_pt = Column(Text)  # Generated summary in Portuguese
    recommendations = Column(JSON)  # Array of recommendation objects
    
    status = Column(String(20), nullable=False, default="final")  # preliminary, final, corrected
    issued_at = Column(DateTime(timezone=True), index=True)
    effective_period_start = Column(DateTime(timezone=True))
    effective_period_end = Column(DateTime(timezone=True))
    
    performer_org_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_json = Column(JSON)
    
    # Relationships
    patient = relationship("Patient", back_populates="reports")
    document = relationship("Document", back_populates="reports")
    extraction_job = relationship("ExtractionJob", back_populates="reports")
    performer_organization = relationship("Organization")