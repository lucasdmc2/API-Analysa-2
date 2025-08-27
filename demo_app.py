"""
Demo version of API de Extração e Normalização de Exames Clínicos
Simplified version that works without database dependencies
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import uuid

# FastAPI app
app = FastAPI(
    title="API de Extração e Normalização de Exames Clínicos - DEMO",
    description="""
    **VERSÃO DEMO** - API determinística para ingestão de laudos de exames (PDF/imagem),
    extração OCR, normalização LOINC/UCUM, cálculo de flags e geração de 
    recomendações informativas para o contexto brasileiro.
    
    ## Características Principais
    - **Determinismo**: Mesmo input → mesmo output (cache por hash)
    - **Auditabilidade**: Trilha completa de processamento  
    - **Interoperabilidade**: LOINC, UCUM, SNOMED CT
    - **Conformidade LGPD**: Dados em território brasileiro
    
    ## Autenticação Demo
    Use os tokens de desenvolvimento:
    - `dev-admin` - Acesso administrativo completo
    - `dev-user` - Usuário regular (read/write)
    - `dev-read` - Somente leitura
    """,
    version="1.0.0-demo",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - Permitir todas as origens para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens
    allow_credentials=False,  # Desativar credentials para permitir "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Mock data stores
mock_ingestions = {}
mock_reports = {}
mock_patients = {}
mock_observations = {}
mock_rangesets = {}

# Schemas
class User(BaseModel):
    user_id: str
    tenant_id: str
    scopes: List[str]
    email: Optional[str] = None
    name: Optional[str] = None

class CreateIngestionRequest(BaseModel):
    document_type: str = Field(..., pattern=r"^(laboratory_report|imaging_report)$")
    patient_id: Optional[str] = None
    filename: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestionResponse(BaseModel):
    ingestion_id: str
    status: str
    created_at: datetime
    upload_url: Optional[str] = None

class Patient(BaseModel):
    patient_id: str
    age_years: Optional[int] = None
    sex: Optional[str] = None

class Observation(BaseModel):
    observation_id: str
    loinc_code: Optional[str] = None
    display: str
    value_numeric: Optional[float] = None
    unit_ucum: Optional[str] = None
    flag: Optional[str] = None
    collected_at: Optional[datetime] = None

class Recommendation(BaseModel):
    code: str
    text: str
    level: str
    disclaimer: str = "Esta recomendação é informativa e não substitui avaliação médica."

class ReportResponse(BaseModel):
    report_id: str
    patient: Patient
    observations: List[Observation]
    summary_pt: Optional[str] = None
    recommendations: List[Recommendation] = Field(default_factory=list)
    created_at: datetime

class CreateRangesetRequest(BaseModel):
    analyte_key: str
    loinc_code: Optional[str] = None
    unit_ucum: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    sex: str = "all"
    confidence_level: str = "medium"

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    dependencies: Dict[str, str]

# Auth functions
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Mock users
    mock_users = {
        "dev-admin": User(
            user_id="admin-001",
            tenant_id="00000000-0000-0000-0000-000000000000",
            scopes=["read", "write", "admin"],
            email="admin@clinical-extraction.com",
            name="Admin User"
        ),
        "dev-user": User(
            user_id="user-001",
            tenant_id="00000000-0000-0000-0000-000000000000", 
            scopes=["read", "write"],
            email="user@clinical-extraction.com",
            name="Regular User"
        ),
        "dev-read": User(
            user_id="read-001",
            tenant_id="00000000-0000-0000-0000-000000000000",
            scopes=["read"],
            email="read@clinical-extraction.com",
            name="Read Only User"
        ),
    }
    
    if token not in mock_users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
        )
    
    return mock_users[token]

def require_scope(required_scope: str):
    async def _require_scope(current_user: User = Depends(get_current_user)):
        if required_scope not in current_user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operação requer escopo '{required_scope}'",
            )
        return None
    return _require_scope

# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificação de saúde da API"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0-demo",
        dependencies={
            "database": "mock",
            "storage": "mock", 
            "ocr_service": "mock"
        }
    )

# Documentation endpoint
@app.get("/api-docs", response_class=HTMLResponse)
async def api_documentation():
    """Documentação simplificada da API"""
    try:
        with open("api_documentation.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>API de Extração e Normalização de Exames Clínicos</h1>
                <p>Documentação não encontrada. Use <a href="/docs">/docs</a> para Swagger UI.</p>
                <p>Teste: <a href="/health">/health</a></p>
            </body>
        </html>
        """)

# Ingestion endpoints
@app.post("/v1/ingestions", response_model=IngestionResponse, status_code=201)
async def create_ingestion(
    request: CreateIngestionRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("write")),
):
    """Criar nova ingestão de documento"""
    
    ingestion_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    ingestion = {
        "ingestion_id": ingestion_id,
        "status": "processing",
        "document_type": request.document_type,
        "patient_id": request.patient_id,
        "filename": request.filename,
        "metadata": request.metadata,
        "created_at": timestamp,
        "tenant_id": current_user.tenant_id,
    }
    
    mock_ingestions[ingestion_id] = ingestion
    
    # Simulate creating a mock report
    if request.patient_id:
        patient_id = request.patient_id
    else:
        patient_id = str(uuid.uuid4())
        
    # Create mock patient if not exists
    if patient_id not in mock_patients:
        mock_patients[patient_id] = {
            "patient_id": patient_id,
            "age_years": 45,
            "sex": "female",
        }
    
    # Create mock report
    report_id = str(uuid.uuid4())
    mock_reports[report_id] = {
        "report_id": report_id,
        "ingestion_id": ingestion_id,
        "patient_id": patient_id,
        "document_type": request.document_type,
        "created_at": timestamp,
    }
    
    return IngestionResponse(
        ingestion_id=ingestion_id,
        status="processing",
        created_at=timestamp,
        upload_url=f"https://s3.clinical-bucket.com.br/upload/{ingestion_id}" if request.filename else None,
    )

@app.get("/v1/ingestions/{ingestion_id}")
async def get_ingestion(
    ingestion_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("read")),
):
    """Consultar status da ingestão"""
    
    if ingestion_id not in mock_ingestions:
        raise HTTPException(status_code=404, detail="Ingestão não encontrada")
    
    ingestion = mock_ingestions[ingestion_id]
    
    return {
        "ingestion_id": ingestion_id,
        "status": "completed",
        "pipeline_version": "1.0.0",
        "progress_percent": 100,
        "created_at": ingestion["created_at"],
        "completed_at": datetime.now(),
    }

# Reports endpoints
@app.get("/v1/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("read")),
):
    """Obter laudo estruturado"""
    
    if report_id not in mock_reports:
        raise HTTPException(status_code=404, detail="Laudo não encontrado")
    
    report = mock_reports[report_id]
    patient = mock_patients[report["patient_id"]]
    
    # Mock observations
    observations = [
        Observation(
            observation_id=str(uuid.uuid4()),
            loinc_code="718-7",
            display="Hemoglobina",
            value_numeric=13.2,
            unit_ucum="g/dL",
            flag="N",
            collected_at=datetime.now(),
        ),
        Observation(
            observation_id=str(uuid.uuid4()),
            loinc_code="2345-7", 
            display="Glicose",
            value_numeric=105.0,
            unit_ucum="mg/dL",
            flag="H",
            collected_at=datetime.now(),
        ),
    ]
    
    recommendations = [
        Recommendation(
            code="GLUCOSE_ELEVATED_MILD",
            text="Glicose levemente elevada. Recomenda-se discutir com seu médico sobre possível repetição do exame.",
            level="attention",
        )
    ]
    
    return ReportResponse(
        report_id=report_id,
        patient=Patient(**patient),
        observations=observations,
        summary_pt="Seus exames mostram hemoglobina dentro da normalidade (13.2 g/dL). A glicose está levemente elevada (105 mg/dL).",
        recommendations=recommendations,
        created_at=report["created_at"],
    )

# Patients endpoints  
@app.get("/v1/patients/{patient_id}/observations")
async def get_patient_observations(
    patient_id: str,
    loinc_code: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("read")),
):
    """Listar observações do paciente"""
    
    if patient_id not in mock_patients:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    # Mock observations
    observations = [
        {
            "observation_id": str(uuid.uuid4()),
            "loinc_code": "718-7",
            "display": "Hemoglobina", 
            "value_numeric": 13.2,
            "unit_ucum": "g/dL",
            "flag": "N",
            "collected_at": datetime.now(),
        },
        {
            "observation_id": str(uuid.uuid4()),
            "loinc_code": "2345-7",
            "display": "Glicose",
            "value_numeric": 105.0,
            "unit_ucum": "mg/dL", 
            "flag": "H",
            "collected_at": datetime.now(),
        },
    ]
    
    # Filter by LOINC if provided
    if loinc_code:
        observations = [obs for obs in observations if obs["loinc_code"] == loinc_code]
    
    return {
        "data": observations[:limit],
        "pagination": {
            "has_next": False,
            "limit": limit,
        }
    }

# Admin endpoints
@app.post("/v1/admin/rangesets", status_code=201)
async def create_rangeset(
    request: CreateRangesetRequest,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("admin")),
):
    """Criar faixa de referência"""
    
    rangeset_id = str(uuid.uuid4())
    
    rangeset = {
        "rangeset_id": rangeset_id,
        "analyte_key": request.analyte_key,
        "loinc_code": request.loinc_code,
        "unit_ucum": request.unit_ucum,
        "ref_low": request.ref_low,
        "ref_high": request.ref_high,
        "sex": request.sex,
        "confidence_level": request.confidence_level,
        "created_at": datetime.now(),
    }
    
    mock_rangesets[rangeset_id] = rangeset
    
    return rangeset

@app.get("/v1/admin/rangesets")
async def list_rangesets(
    analyte_key: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_scope("read")),
):
    """Listar faixas de referência"""
    
    rangesets = list(mock_rangesets.values())
    
    # Filter by analyte_key if provided
    if analyte_key:
        rangesets = [rs for rs in rangesets if rs["analyte_key"] == analyte_key]
    
    return {
        "data": rangesets[:limit],
        "pagination": {
            "has_next": False,
            "limit": limit,
        }
    }

# ============================================================================
# STATIC FILES AND WEB CLIENT
# ============================================================================

@app.get("/client", response_class=HTMLResponse)
async def web_client():
    """Serve the web client interface"""
    try:
        with open("/workspace/api_web_client.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html><body>
            <h1>Cliente Web não encontrado</h1>
            <p>O arquivo api_web_client.html não foi encontrado.</p>
            <p><a href="/docs">Acesse a documentação da API</a></p>
            </body></html>
            """,
            status_code=404
        )

@app.get("/client-offline", response_class=HTMLResponse)
async def web_client_offline():
    """Serve the offline web client interface"""
    try:
        with open("/workspace/cliente_web_offline.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
            <html><body>
            <h1>Cliente Web Offline não encontrado</h1>
            <p>O arquivo cliente_web_offline.html não foi encontrado.</p>
            <p><a href="/client">Acesse o cliente web normal</a></p>
            </body></html>
            """,
            status_code=404
        )

@app.get("/download-client")
async def download_client():
    """Download the offline client for local use"""
    try:
        return FileResponse(
            path="/workspace/cliente_web_offline.html",
            filename="cliente_web_offline.html",
            media_type="text/html"
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

@app.get("/")
async def root():
    """Root endpoint with links to all interfaces"""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>API de Exames Clínicos - DEMO</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c5282; text-align: center; }}
            .links {{ display: grid; gap: 20px; margin-top: 30px; }}
            .link-card {{ background: #e2e8f0; padding: 20px; border-radius: 8px; text-decoration: none; color: #2d3748; border-left: 5px solid #3182ce; }}
            .link-card:hover {{ background: #cbd5e0; transform: translateY(-2px); transition: all 0.2s; }}
            .status {{ background: #c6f6d5; color: #22543d; padding: 10px; border-radius: 5px; margin: 20px 0; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🩺 API de Extração e Normalização de Exames Clínicos</h1>
            <div class="status">✅ API Online - Versão Demo</div>
            
            <div class="links">
                <a href="/client" class="link-card">
                    <h3>🌐 Cliente Web Interativo</h3>
                    <p>Interface gráfica completa para testar todos os endpoints da API</p>
                </a>
                
                <a href="/client-offline" class="link-card">
                    <h3>💾 Cliente Web Offline</h3>
                    <p>Versão que funciona mesmo sem conexão (com dados demo)</p>
                </a>
                
                <a href="/download-client" class="link-card">
                    <h3>📥 Download Cliente Offline</h3>
                    <p>Baixar arquivo HTML para usar localmente no seu computador</p>
                </a>
                
                <a href="/docs" class="link-card">
                    <h3>📚 Documentação Swagger</h3>
                    <p>Documentação interativa da API com exemplos</p>
                </a>
                
                <a href="/redoc" class="link-card">
                    <h3>📖 Documentação ReDoc</h3>
                    <p>Documentação alternativa da API</p>
                </a>
                
                <a href="/health" class="link-card">
                    <h3>❤️ Health Check</h3>
                    <p>Verificar status e saúde da API</p>
                </a>
                
                <a href="/api-docs" class="link-card">
                    <h3>📄 Documentação HTML</h3>
                    <p>Documentação estática em HTML</p>
                </a>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: #666;">
                <p>Desenvolvido para extração e normalização de exames clínicos (Brasil)</p>
                <p>Suporte: LOINC, UCUM, SNOMED CT, CID-10</p>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)