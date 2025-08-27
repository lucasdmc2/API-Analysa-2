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

@app.get("/swagger", response_class=HTMLResponse)
async def swagger_redirect():
    """Redirect to Swagger UI for easy access"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecionando para Swagger UI...</title>
        <meta http-equiv="refresh" content="0; url=/docs">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            h1 { color: #1976d2; }
            .loading { margin: 20px 0; }
            a { color: #1976d2; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Redirecionando para Swagger UI</h1>
            <div class="loading">Carregando documentação interativa...</div>
            <p>Se não for redirecionado automaticamente, <a href="/docs">clique aqui</a></p>
        </div>
        <script>
            setTimeout(function() {
                window.location.href = '/docs';
            }, 1000);
        </script>
    </body>
    </html>
    """)

@app.get("/swagger-info", response_class=HTMLResponse)
async def swagger_info():
    """Information about how to use Swagger UI"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Como Usar o Swagger UI - API de Exames Clínicos</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 50px; background: #f5f5f5; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            h1 { color: #1976d2; text-align: center; }
            h2 { color: #2c5282; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
            .btn { background: #1976d2; color: white; padding: 12px 24px; border: none; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 5px; }
            .btn:hover { background: #1565c0; }
            .code { background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #1976d2; font-family: monospace; }
            .feature { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Como Usar o Swagger UI</h1>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/docs" class="btn">🔗 Abrir Swagger UI</a>
                <a href="/redoc" class="btn">📖 Abrir ReDoc</a>
                <a href="/" class="btn">🏠 Página Principal</a>
            </div>
            
            <h2>📋 O que é o Swagger UI?</h2>
            <p>O Swagger UI é uma interface interativa que permite:</p>
            <ul>
                <li><strong>Visualizar</strong> todos os endpoints da API</li>
                <li><strong>Testar</strong> requisições diretamente no navegador</li>
                <li><strong>Ver</strong> exemplos de requests e responses</li>
                <li><strong>Entender</strong> a estrutura de dados da API</li>
                <li><strong>Experimentar</strong> diferentes parâmetros e payloads</li>
            </ul>
            
            <h2>🔧 Como Usar</h2>
            
            <div class="feature">
                <h3>1. Autenticação</h3>
                <p>Use um dos tokens demo para autenticação:</p>
                <div class="code">
                    dev-admin (acesso completo)<br>
                    dev-user (read/write)<br>
                    dev-read (somente leitura)
                </div>
                <p>Clique no botão "Authorize" no Swagger UI e digite: <code>Bearer dev-user</code></p>
            </div>
            
            <div class="feature">
                <h3>2. Endpoints Disponíveis</h3>
                <ul>
                    <li><strong>GET /health</strong> - Status da API</li>
                    <li><strong>POST /v1/ingestions</strong> - Criar ingestão</li>
                    <li><strong>GET /v1/ingestions/{id}</strong> - Status da ingestão</li>
                    <li><strong>GET /v1/patients/{id}/observations</strong> - Observações do paciente</li>
                    <li><strong>POST /v1/admin/rangesets</strong> - Criar faixa de referência</li>
                    <li><strong>GET /v1/admin/rangesets</strong> - Listar faixas</li>
                </ul>
            </div>
            
            <div class="feature">
                <h3>3. Testando Endpoints</h3>
                <p>Para testar um endpoint:</p>
                <ol>
                    <li>Clique no endpoint desejado</li>
                    <li>Clique em "Try it out"</li>
                    <li>Preencha os parâmetros necessários</li>
                    <li>Clique em "Execute"</li>
                    <li>Veja a resposta na seção "Response"</li>
                </ol>
            </div>
            
            <h2>📊 Dados Demo</h2>
            <p>Use estes dados para testar:</p>
            
            <div class="feature">
                <h3>Paciente ID:</h3>
                <div class="code">123e4567-e89b-12d3-a456-426614174000</div>
            </div>
            
            <div class="feature">
                <h3>Exemplo de Ingestão:</h3>
                <div class="code">
{<br>
  "document_type": "laboratory_report",<br>
  "filename": "hemograma.pdf",<br>
  "patient_id": "123e4567-e89b-12d3-a456-426614174000"<br>
}
                </div>
            </div>
            
            <div class="feature">
                <h3>Exemplo de Faixa de Referência:</h3>
                <div class="code">
{<br>
  "analyte_key": "glucose_test",<br>
  "unit_ucum": "mg/dL",<br>
  "ref_low": 70,<br>
  "ref_high": 99<br>
}
                </div>
            </div>
            
            <h2>🌐 Acesso</h2>
            <p>URLs disponíveis:</p>
            <ul>
                <li><strong>Swagger UI:</strong> <a href="/docs">/docs</a></li>
                <li><strong>ReDoc:</strong> <a href="/redoc">/redoc</a></li>
                <li><strong>OpenAPI Schema:</strong> <a href="/openapi.json">/openapi.json</a></li>
                <li><strong>Esta Página:</strong> <a href="/swagger-info">/swagger-info</a></li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0; padding: 20px; background: #f0f8ff; border-radius: 5px;">
                <h3>🚀 Pronto para começar?</h3>
                <a href="/docs" class="btn">Usar Swagger UI Agora</a>
            </div>
        </div>
    </body>
    </html>
    """)

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
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c5282; text-align: center; }}
            .links {{ display: grid; gap: 20px; margin-top: 30px; }}
            .link-card {{ background: #e2e8f0; padding: 20px; border-radius: 8px; text-decoration: none; color: #2d3748; border-left: 5px solid #3182ce; }}
            .link-card:hover {{ background: #cbd5e0; transform: translateY(-2px); transition: all 0.2s; }}
            .link-card.swagger {{ background: #f0f8ff; border-left: 5px solid #1976d2; }}
            .link-card.swagger:hover {{ background: #e3f2fd; }}
            .status {{ background: #c6f6d5; color: #22543d; padding: 10px; border-radius: 5px; margin: 20px 0; text-align: center; }}
            .swagger-section {{ background: #f8fafc; padding: 25px; border-radius: 10px; margin: 25px 0; border: 2px solid #1976d2; }}
            .swagger-section h2 {{ color: #1976d2; text-align: center; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🩺 API de Extração e Normalização de Exames Clínicos</h1>
            <div class="status">✅ API Online - Versão Demo</div>
            
            <div class="swagger-section">
                <h2>📋 Swagger UI - Documentação Interativa</h2>
                <div class="links">
                    <a href="/docs" class="link-card swagger">
                        <h3>🚀 Swagger UI</h3>
                        <p><strong>PRINCIPAL:</strong> Interface interativa para testar todos os endpoints da API</p>
                    </a>
                    
                    <a href="/redoc" class="link-card swagger">
                        <h3>📖 ReDoc</h3>
                        <p>Documentação alternativa com visual limpo e organizado</p>
                    </a>
                    
                    <a href="/openapi.json" class="link-card swagger">
                        <h3>⚙️ OpenAPI Schema</h3>
                        <p>Schema JSON para importar em Postman, Insomnia ou outras ferramentas</p>
                    </a>
                    
                    <a href="/swagger-info" class="link-card swagger">
                        <h3>📚 Guia do Swagger UI</h3>
                        <p>Tutorial completo de como usar a documentação interativa</p>
                    </a>
                </div>
            </div>
            
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
                <p><strong>🚀 Use o Swagger UI em /docs para testar interativamente!</strong></p>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)