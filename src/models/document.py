"""
SQLAlchemy models for documents and extraction jobs
"""

from sqlalchemy import Column, String, BigInteger, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.db.database import Base


class Document(Base):
    """Document model for uploaded files"""
    __tablename__ = "document"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sha256 = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    original_filename = Column(Text)
    ingest_source = Column(String(50), nullable=False, default="upload")
    status = Column(String(20), nullable=False, default="uploaded", index=True)
    s3_bucket = Column(String(100))
    s3_key = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default={})
    
    # Relationships
    extraction_jobs = relationship("ExtractionJob", back_populates="document", cascade="all, delete-orphan")
    lab_tests = relationship("LabTest", back_populates="document")
    reports = relationship("Report", back_populates="document")


class ExtractionJob(Base):
    """Extraction job model for processing pipeline runs"""
    __tablename__ = "extraction_job"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("document.id"), nullable=False, index=True)
    pipeline_version = Column(String(20), nullable=False, index=True)
    config_hash = Column(String(64), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="running", index=True)
    error_message = Column(Text)
    artifacts_s3_prefix = Column(Text)
    cache_hit = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="extraction_jobs")
    lab_tests = relationship("LabTest", back_populates="extraction_job")
    reports = relationship("Report", back_populates="extraction_job")