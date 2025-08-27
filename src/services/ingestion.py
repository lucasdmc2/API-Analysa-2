"""
Ingestion service for document upload and processing
"""

import hashlib
import uuid
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import structlog

from src.models.document import Document, ExtractionJob
from src.schemas.ingestion import (
    CreateIngestionRequest, IngestionResponse, IngestionStatus, IngestionProgress
)
from src.core.config import settings
from src.core.exceptions import ResourceNotFoundError, ProcessingInProgressError
from src.db.database import set_tenant_context

logger = structlog.get_logger()


class IngestionService:
    """Service for handling document ingestion and processing"""
    
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        set_tenant_context(db, str(tenant_id))
    
    async def create_direct_ingestion(
        self, 
        request: CreateIngestionRequest, 
        file_content: bytes
    ) -> IngestionResponse:
        """Create ingestion with direct file upload"""
        
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for existing document
        existing_doc = self.db.query(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.sha256 == file_hash
        ).first()
        
        if existing_doc:
            logger.info("Document already exists", document_id=existing_doc.id, sha256=file_hash)
            # Return existing ingestion or create new processing job
            return await self._handle_existing_document(existing_doc, request)
        
        # Create new document
        document = Document(
            tenant_id=self.tenant_id,
            sha256=file_hash,
            mime_type=self._detect_mime_type(file_content),
            file_size_bytes=len(file_content),
            original_filename=request.filename,
            ingest_source="upload",
            status="uploaded",
            metadata=request.metadata,
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # TODO: Upload file to S3
        # await self._upload_to_s3(document.id, file_content)
        
        logger.info(
            "Document uploaded successfully",
            document_id=document.id,
            tenant_id=self.tenant_id,
            file_size=len(file_content)
        )
        
        return IngestionResponse(
            ingestion_id=document.id,
            status="created",
            created_at=document.created_at,
        )
    
    async def create_presigned_ingestion(
        self, 
        request: CreateIngestionRequest
    ) -> IngestionResponse:
        """Create ingestion with pre-signed URL for upload"""
        
        # Create placeholder document
        document = Document(
            tenant_id=self.tenant_id,
            sha256="",  # Will be set after upload
            mime_type="application/octet-stream",  # Will be detected after upload
            file_size_bytes=0,  # Will be set after upload
            original_filename=request.filename,
            ingest_source="upload",
            status="uploading",
            metadata=request.metadata,
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # TODO: Generate pre-signed S3 URL
        upload_url = f"https://s3.amazonaws.com/{settings.S3_BUCKET_NAME}/upload/{document.id}"
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        return IngestionResponse(
            ingestion_id=document.id,
            status="uploading",
            upload_url=upload_url,
            expires_at=expires_at,
            created_at=document.created_at,
        )
    
    async def get_ingestion_status(self, ingestion_id: uuid.UUID) -> IngestionStatus:
        """Get current status of ingestion"""
        
        document = self.db.query(Document).filter(
            Document.id == ingestion_id,
            Document.tenant_id == self.tenant_id
        ).first()
        
        if not document:
            raise ResourceNotFoundError("Document", str(ingestion_id))
        
        # Get latest extraction job
        latest_job = self.db.query(ExtractionJob).filter(
            ExtractionJob.document_id == document.id
        ).order_by(ExtractionJob.created_at.desc()).first()
        
        return IngestionStatus(
            ingestion_id=document.id,
            document_id=document.id,
            status=document.status,
            pipeline_version=latest_job.pipeline_version if latest_job else None,
            progress=self._get_progress(latest_job) if latest_job else None,
            error_message=latest_job.error_message if latest_job else None,
            artifacts=[],  # TODO: Load from S3
            created_at=document.created_at,
            completed_at=latest_job.ended_at if latest_job else None,
        )
    
    async def finalize_ingestion(self, ingestion_id: uuid.UUID) -> IngestionStatus:
        """Finalize pre-signed URL upload and prepare for processing"""
        
        document = self.db.query(Document).filter(
            Document.id == ingestion_id,
            Document.tenant_id == self.tenant_id
        ).first()
        
        if not document:
            raise ResourceNotFoundError("Document", str(ingestion_id))
        
        # TODO: Verify S3 upload completed and update document metadata
        # file_metadata = await self._verify_s3_upload(document.id)
        # document.sha256 = file_metadata.sha256
        # document.file_size_bytes = file_metadata.size
        # document.mime_type = file_metadata.mime_type
        
        document.status = "uploaded"
        self.db.commit()
        
        return await self.get_ingestion_status(ingestion_id)
    
    async def start_processing(self, document_id: uuid.UUID):
        """Start processing pipeline (background task)"""
        
        try:
            # Check for existing processing job
            existing_job = self.db.query(ExtractionJob).filter(
                ExtractionJob.document_id == document_id,
                ExtractionJob.status == "running"
            ).first()
            
            if existing_job:
                raise ProcessingInProgressError(str(document_id))
            
            # Create new extraction job
            extraction_job = ExtractionJob(
                document_id=document_id,
                pipeline_version=settings.PIPELINE_VERSION,
                config_hash=self._generate_config_hash(),
                status="running",
            )
            
            self.db.add(extraction_job)
            self.db.commit()
            
            # TODO: Start actual processing pipeline
            # await self._run_extraction_pipeline(extraction_job.id)
            
            logger.info(
                "Processing started",
                document_id=document_id,
                job_id=extraction_job.id
            )
            
        except Exception as e:
            logger.error(
                "Failed to start processing",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
    
    def _detect_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type from file content"""
        # Simple detection based on magic bytes
        if file_content.startswith(b'%PDF'):
            return 'application/pdf'
        elif file_content.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif file_content.startswith(b'\x89PNG'):
            return 'image/png'
        else:
            return 'application/octet-stream'
    
    def _generate_config_hash(self) -> str:
        """Generate hash of current processing configuration"""
        config_str = f"{settings.PIPELINE_VERSION}:{settings.OCR_CONFIDENCE_THRESHOLD}"
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def _get_progress(self, job: ExtractionJob) -> Optional[IngestionProgress]:
        """Get processing progress from job"""
        if not job or job.status != "running":
            return None
        
        # TODO: Implement actual progress tracking
        return IngestionProgress(
            current_step="ocr",
            progress_percent=25
        )
    
    async def _handle_existing_document(
        self, 
        document: Document, 
        request: CreateIngestionRequest
    ) -> IngestionResponse:
        """Handle case where document already exists"""
        
        # Check if already processed or processing
        latest_job = self.db.query(ExtractionJob).filter(
            ExtractionJob.document_id == document.id
        ).order_by(ExtractionJob.created_at.desc()).first()
        
        if latest_job and latest_job.status == "completed":
            # Document already processed, return cache hit
            return IngestionResponse(
                ingestion_id=document.id,
                status="completed",
                created_at=document.created_at,
            )
        
        # Start new processing if needed
        return IngestionResponse(
            ingestion_id=document.id,
            status="processing",
            created_at=document.created_at,
        )