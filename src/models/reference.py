"""
SQLAlchemy models for reference data (ranges, mappings, organizations)
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Numeric, Date, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.db.database import Base


class Organization(Base):
    """Organization model for labs, hospitals, clinics"""
    __tablename__ = "organization"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(Text, nullable=False)
    identifier = Column(String(100), index=True)  # CNPJ, CNES, etc
    org_type = Column(String(50), nullable=False)  # laboratory, hospital, clinic
    contact_info = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RangeSet(Base):
    """Reference ranges by lab/profile"""
    __tablename__ = "rangeset"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    analyte_key = Column(String(100), nullable=False, index=True)
    loinc_code = Column(String(10), index=True)
    lab_org_id = Column(UUID(as_uuid=True), ForeignKey("organization.id"), index=True)
    
    # Stratifiers for range selection
    age_min_years = Column(Integer)
    age_max_years = Column(Integer)
    sex = Column(String(10))  # male, female, all
    pregnancy_status = Column(String(20))  # pregnant, not_pregnant, all
    method_name = Column(Text)
    
    # Range values
    ref_low = Column(Numeric(20, 6))
    ref_high = Column(Numeric(20, 6))
    ref_text = Column(Text)
    unit_ucum = Column(String(50), nullable=False)
    
    # Metadata
    source = Column(String(100))  # lab, consensus, literature
    effective_start = Column(Date, nullable=False, server_default=func.current_date())
    effective_end = Column(Date)
    confidence_level = Column(String(10), default="medium")  # low, medium, high
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    lab_organization = relationship("Organization")


class LoincMapping(Base):
    """LOINC mapping for lab codes"""
    __tablename__ = "mapping_loinc"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    lab_code = Column(String(100), nullable=False, index=True)
    lab_name = Column(Text, nullable=False)
    loinc_code = Column(String(10), nullable=False, index=True)
    loinc_display = Column(Text, nullable=False)
    confidence = Column(Numeric(3, 2), nullable=False, default=1.00)  # 0.00-1.00
    method_constraint = Column(Text)  # If mapping depends on method
    unit_constraint = Column(String(50))  # If mapping depends on unit
    mapping_rules = Column(JSON)  # Additional rules for mapping
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    validated_at = Column(DateTime(timezone=True))
    validated_by = Column(String(100))


class AuditEvent(Base):
    """Immutable audit trail"""
    __tablename__ = "audit_event"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # document_uploaded, extraction_started, etc
    resource_type = Column(String(50), nullable=False, index=True)  # document, patient, lab_test, etc
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    actor_id = Column(String(100))  # User/system that triggered event
    actor_type = Column(String(20), nullable=False, default="user")  # user, system, api_key
    
    event_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    correlation_id = Column(UUID(as_uuid=True), index=True)  # For tracing related events
    
    # Event details
    action = Column(String(50), nullable=False)  # created, updated, deleted, accessed
    outcome = Column(String(20), nullable=False, default="success")  # success, failure
    details = Column(JSON)
    
    # Security
    ip_address = Column(String(45))  # IPv4/IPv6
    user_agent = Column(Text)