# Error Catalog - API de Extração e Normalização de Exames Clínicos

Este catálogo segue o padrão RFC 7807 (Problem Details for HTTP APIs).

## Formato Padrão de Erro

```json
{
  "type": "https://api.clinical-extraction.com/errors/{error-type}",
  "title": "Título legível do erro",
  "status": 400,
  "detail": "Descrição detalhada do problema",
  "instance": "/v1/ingestions/123",
  "correlation_id": "req-456-789",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Códigos de Erro por Categoria

### 4xx - Erros do Cliente

#### 400 - Bad Request

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `VAL_001` | validation-error | Dados de entrada inválidos | Campo obrigatório ausente | Verificar schema da requisição |
| `VAL_002` | invalid-file-format | Formato de arquivo não suportado | PDF corrompido ou formato não reconhecido | Enviar PDF válido ou imagem |
| `VAL_003` | file-too-large | Arquivo muito grande | Arquivo > 50MB | Reduzir tamanho do arquivo |
| `VAL_004` | invalid-loinc-code | Código LOINC inválido | Formato incorreto (deve ser XXXXX-X) | Usar código LOINC válido |
| `VAL_005` | invalid-date-range | Intervalo de datas inválido | Data inicial > data final | Corrigir intervalo de datas |

#### 401 - Unauthorized

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `AUTH_001` | token-missing | Token de acesso ausente | Header Authorization não enviado | Incluir Bearer token |
| `AUTH_002` | token-invalid | Token de acesso inválido | Token malformado ou expirado | Renovar token de acesso |
| `AUTH_003` | token-expired | Token de acesso expirado | Token válido mas expirado | Renovar token de acesso |

#### 403 - Forbidden

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `AUTHZ_001` | insufficient-scope | Escopo insuficiente | Token não tem permissão necessária | Solicitar token com escopo adequado |
| `AUTHZ_002` | tenant-access-denied | Acesso ao tenant negado | Tentativa de acessar dados de outro tenant | Verificar tenant_id |
| `AUTHZ_003` | admin-required | Acesso administrativo necessário | Endpoint requer papel de admin | Solicitar acesso administrativo |

#### 404 - Not Found

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `RES_001` | resource-not-found | Recurso não encontrado | ID não existe ou foi deletado | Verificar ID do recurso |
| `RES_002` | patient-not-found | Paciente não encontrado | patient_id inválido | Verificar ID do paciente |
| `RES_003` | report-not-found | Laudo não encontrado | report_id inválido | Verificar ID do laudo |

#### 409 - Conflict

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `CONF_001` | duplicate-resource | Recurso duplicado | Tentativa de criar recurso existente | Usar recurso existente ou atualizar |
| `CONF_002` | processing-in-progress | Processamento em andamento | Documento já sendo processado | Aguardar conclusão |

#### 429 - Too Many Requests

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `RATE_001` | rate-limit-exceeded | Limite de requisições excedido | Muitas requisições em pouco tempo | Aguardar Retry-After segundos |
| `RATE_002` | quota-exceeded | Cota mensal excedida | Limite de processamento mensal atingido | Aguardar próximo ciclo ou upgrade |

### 5xx - Erros do Servidor

#### 500 - Internal Server Error

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `SRV_001` | internal-error | Erro interno do servidor | Falha não esperada no sistema | Contatar suporte com correlation_id |
| `SRV_002` | processing-failed | Falha no processamento | Erro no pipeline de extração | Tentar novamente ou contatar suporte |

#### 503 - Service Unavailable

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `SVC_001` | ocr-service-unavailable | Serviço OCR indisponível | AWS Textract com problemas | Aguardar restauração ou tentar novamente |
| `SVC_002` | database-unavailable | Banco de dados indisponível | PostgreSQL com problemas | Aguardar restauração |
| `SVC_003` | storage-unavailable | Armazenamento indisponível | S3 com problemas | Aguardar restauração |

#### 504 - Gateway Timeout

| Código | Type | Título | Causa Comum | Resolução |
|--------|------|--------|-------------|-----------|
| `TMO_001` | processing-timeout | Timeout no processamento | Documento muito complexo | Tentar novamente com documento menor |
| `TMO_002` | ocr-timeout | Timeout no OCR | Imagem de baixa qualidade | Melhorar qualidade da imagem |

## Códigos Específicos do Domínio

### Extração e OCR

| Código | Type | Título | Descrição | Resolução |
|--------|------|--------|-----------|-----------|
| `OCR_001` | ocr-quality-low | Qualidade OCR insuficiente | Texto não legível | Melhorar qualidade da imagem |
| `OCR_002` | no-tables-found | Nenhuma tabela encontrada | Layout não reconhecido | Verificar formato do laudo |
| `OCR_003` | extraction-confidence-low | Confiança da extração baixa | Valores ambíguos | Revisão manual necessária |

### Normalização

| Código | Type | Título | Descrição | Resolução |
|--------|------|--------|-----------|-----------|
| `NORM_001` | loinc-mapping-failed | Falha no mapeamento LOINC | Analito não mapeado | Configurar mapeamento manual |
| `NORM_002` | unit-conversion-failed | Falha na conversão de unidades | Unidade não reconhecida | Verificar unidades UCUM |
| `NORM_003` | reference-range-missing | Faixa de referência ausente | Sem faixa para perfil do paciente | Configurar faixa específica |

### Cache e Determinismo

| Código | Type | Título | Descrição | Resolução |
|--------|------|--------|-----------|-----------|
| `CACHE_001` | pipeline-version-mismatch | Versão do pipeline incompatível | Pipeline atualizado | Reprocessar com nova versão |
| `CACHE_002` | determinism-failure | Falha no determinismo | Outputs diferentes para mesmo input | Reportar bug crítico |

## Exemplos de Respostas de Erro

### Arquivo inválido
```json
{
  "type": "https://api.clinical-extraction.com/errors/invalid-file-format",
  "title": "Formato de arquivo não suportado",
  "status": 400,
  "detail": "O arquivo deve ser um PDF válido ou imagem nos formatos JPEG, PNG",
  "instance": "/v1/ingestions",
  "correlation_id": "req-123-456-789",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Token expirado
```json
{
  "type": "https://api.clinical-extraction.com/errors/token-expired",
  "title": "Token de acesso expirado",
  "status": 401,
  "detail": "O token de acesso expirou em 2025-01-15T09:00:00Z",
  "instance": "/v1/reports/abc-123",
  "correlation_id": "req-456-789-012",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Rate limiting
```json
{
  "type": "https://api.clinical-extraction.com/errors/rate-limit-exceeded",
  "title": "Limite de requisições excedido",
  "status": 429,
  "detail": "Limite de 1000 requisições por hora excedido. Tente novamente em 3600 segundos.",
  "instance": "/v1/ingestions",
  "correlation_id": "req-789-012-345",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Falha no OCR
```json
{
  "type": "https://api.clinical-extraction.com/errors/ocr-quality-low",
  "title": "Qualidade OCR insuficiente",
  "status": 422,
  "detail": "Não foi possível extrair texto legível do documento. Verifique a qualidade da imagem.",
  "instance": "/v1/ingestions/def-456",
  "correlation_id": "req-012-345-678",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Headers de Resposta

### Rate Limiting
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
Retry-After: 3600
```

### Correlação e Debug
```
X-Correlation-ID: req-123-456-789
X-Request-ID: abc-def-ghi-jkl
X-Response-Time: 150ms
```

## Monitoramento

### Alertas por Tipo de Erro
- **AUTH_*** : Alertar se > 5% das requisições
- **RATE_*** : Alertar se > 10% das requisições  
- **SRV_*** : Alertar imediatamente
- **OCR_*** : Alertar se > 20% das extrações

### Dashboards
- Taxa de erro por endpoint
- Distribuição de códigos de erro
- Tempo médio de resposta por status
- Correlação entre errors e tenants