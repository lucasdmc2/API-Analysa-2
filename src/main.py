"""
API de Extração e Normalização de Exames Clínicos
FastAPI application entry point
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
import uuid

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.logging import configure_logging
from src.core.exceptions import APIException
from src.db.database import engine

# Configure structured logging
configure_logging()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="API de Extração e Normalização de Exames Clínicos",
    description=(
        "API determinística para ingestão de laudos de exames (PDF/imagem), "
        "extração OCR, normalização LOINC/UCUM, cálculo de flags e "
        "geração de recomendações informativas para o contexto brasileiro."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Add correlation ID and request logging"""
    start_time = time.time()
    
    # Generate correlation ID if not present
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Add to request state
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        correlation_id=correlation_id,
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration=f"{duration:.3f}s",
        correlation_id=correlation_id,
    )
    
    return response


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions following RFC 7807"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        "API exception occurred",
        error_type=exc.error_type,
        title=exc.title,
        detail=exc.detail,
        status_code=exc.status_code,
        correlation_id=correlation_id,
    )
    
    error_response = {
        "type": f"https://api.clinical-extraction.com/errors/{exc.error_type}",
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url),
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.error(
        "Unexpected exception occurred",
        exception=str(exc),
        correlation_id=correlation_id,
        exc_info=True,
    )
    
    error_response = {
        "type": "https://api.clinical-extraction.com/errors/internal-error",
        "title": "Erro interno do servidor",
        "status": 500,
        "detail": "Ocorreu um erro interno. Entre em contato com o suporte.",
        "instance": str(request.url),
        "correlation_id": correlation_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": "1.0.0",
        "dependencies": {
            "database": db_status,
            "storage": "healthy",  # TODO: Implement S3 check
            "ocr_service": "healthy",  # TODO: Implement OCR service check
        },
    }


# Include API router
app.include_router(api_router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_config=None,  # Use our custom logging
    )