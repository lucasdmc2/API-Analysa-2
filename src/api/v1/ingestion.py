"""
Ingestion API endpoints for document upload and processing
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from src.core.exceptions import InvalidFileFormatError, FileTooLargeError
from src.core.config import settings
from src.db.database import get_db
from src.schemas.ingestion import CreateIngestionRequest, IngestionResponse, IngestionStatus
from src.services.ingestion import IngestionService
from src.services.auth import get_current_user, require_scope

router = APIRouter()


@router.post("", response_model=IngestionResponse, status_code=201)
async def create_ingestion(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    document_type: str = Form(...),
    patient_id: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    metadata: Optional[str] = Form("{}"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("write")),
):
    """
    Create new document ingestion.
    
    Supports two modes:
    1. Direct file upload (multipart/form-data with file)
    2. Pre-signed URL upload (application/json without file)
    """
    
    # Validate document type
    if document_type not in ["laboratory_report", "imaging_report"]:
        raise InvalidFileFormatError("document_type must be 'laboratory_report' or 'imaging_report'")
    
    # Validate file if provided
    if file:
        # Check file size
        if file.size and file.size > settings.max_file_size_bytes:
            raise FileTooLargeError(
                f"Arquivo muito grande. Máximo permitido: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Check file type
        allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/tiff"]
        if file.content_type not in allowed_types:
            raise InvalidFileFormatError(
                f"Tipo de arquivo não suportado: {file.content_type}. "
                f"Tipos permitidos: {', '.join(allowed_types)}"
            )
    
    # Create ingestion request
    request = CreateIngestionRequest(
        document_type=document_type,
        patient_id=uuid.UUID(patient_id) if patient_id else None,
        filename=filename or (file.filename if file else None),
        upload_method="direct" if file else "presigned_url",
        metadata=eval(metadata) if metadata != "{}" else {},
    )
    
    # Process ingestion
    ingestion_service = IngestionService(db, current_user.tenant_id)
    
    if file:
        # Direct upload
        file_content = await file.read()
        result = await ingestion_service.create_direct_ingestion(request, file_content)
        
        # Start processing in background
        background_tasks.add_task(
            ingestion_service.start_processing,
            result.ingestion_id
        )
    else:
        # Pre-signed URL upload
        result = await ingestion_service.create_presigned_ingestion(request)
    
    return result


@router.get("/{ingestion_id}", response_model=IngestionStatus)
async def get_ingestion(
    ingestion_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("read")),
):
    """Get ingestion status and artifacts"""
    
    ingestion_service = IngestionService(db, current_user.tenant_id)
    return await ingestion_service.get_ingestion_status(ingestion_id)


@router.post("/{ingestion_id}/finalize", response_model=IngestionStatus)
async def finalize_ingestion(
    ingestion_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_scope("write")),
):
    """
    Finalize upload and start processing.
    Only needed for pre-signed URL uploads.
    """
    
    ingestion_service = IngestionService(db, current_user.tenant_id)
    result = await ingestion_service.finalize_ingestion(ingestion_id)
    
    # Start processing in background
    background_tasks.add_task(
        ingestion_service.start_processing,
        ingestion_id
    )
    
    return result