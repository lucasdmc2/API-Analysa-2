---
title: API de Extração e Normalização de Exames Clínicos - System Specification
version: 1.0.0
mode: mvp
scope: "API determinística para ingestão de laudos de exames (PDF/imagem), extração OCR, normalização LOINC/UCUM, cálculo de flags e geração de recomendações informativas para o contexto brasileiro"
out_of_scope: "Diagnóstico automatizado prescritivo, interpretação pixel-a-pixel de imagens, DICOM SR (P2), HL7/FHIR completo (P1)"
tech_stack_file: ".tech_stack.yaml"
---

# 1. Overview

API REST para extração, normalização e análise de exames clínicos brasileiros com foco em determinismo e auditabilidade. Ingere laudos em PDF/imagem, extrai biomarcadores via OCR, normaliza para terminologias padrão (LOINC/UCUM), compara com faixas de referência e gera recomendações informativas (não prescritivas) compatíveis com LGPD.

**Objetivos principais:**
- Determinismo: mesmo input → mesmo output (cache por hash)
- Auditabilidade: trilha completa de processamento
- Interoperabilidade: LOINC, UCUM, SNOMED CT
- Conformidade LGPD: dados em território brasileiro, consentimento, minimização

# 2. Domain Model

## Core Entities

**Document**
- ID, tenant_id, sha256, mime_type, ingest_source, status, timestamps
- Armazena arquivo original + artefatos OCR

**Patient** 
- ID, tenant_id, external_id, dados demográficos (idade, sexo, gestação)
- Perfil para seleção de faixas de referência

**LabTest (Observation)**
- ID, patient_id, loinc_code, valor numérico/texto, unidade UCUM
- Faixas de referência, flag (L/N/H), timestamps de coleta/resultado

**Report (DiagnosticReport)**
- ID, patient_id, categoria (lab/imaging), conclusão, status

**RangeSet**
- Faixas de referência por laboratório/perfil/analito
- Estratificadores: idade, sexo, gestação, metodologia

**Mapping**
- Mapeamentos laboratório → LOINC com confiança

# 3. API Surface (high-level)

## Ingestão
- `POST /v1/ingestions` - Upload com URL pré-assinado
- `POST /v1/ingestions/{id}/finalize` - Inicia pipeline
- `GET /v1/ingestions/{id}` - Status e artefatos

## Consulta
- `GET /v1/reports/{report_id}` - Laudo estruturado + sumário
- `GET /v1/patients/{id}/observations` - Lista paginada com filtros
- `GET /v1/observations/{id}/visualizations` - Gráficos de tendência

## Administração  
- `POST /v1/admin/rangesets` - CRUD de faixas por laboratório
- `POST /v1/admin/mappings/loinc` - Mapeamentos de analitos

**Autenticação**: OAuth2/OIDC + RBAC (admin, analista, leitura)
**Idempotência**: Header `Idempotency-Key` obrigatório

# 4. Database (high-level)

**PostgreSQL com schemas separados por tenant**

**Core Tables:**
- `document` - Arquivos ingeridos com versionamento
- `extraction_job` - Jobs de processamento com config hash
- `patient` - Demografia e perfil para faixas
- `lab_test` - Observações normalizadas (LOINC/UCUM)
- `report` - Laudos com sumário/recomendações
- `rangeset` - Faixas por laboratório/perfil
- `mapping_loinc` - Dicionário de mapeamentos
- `audit_event` - Trilha imutável append-only

**Storage:**
- Objetos: S3-compatível brasileiro (arquivos + artefatos)
- Cache: Redis para resultados determinísticos
- Vetorial: embeddings para grounding semântico

# 5. Non-Functional Requirements

**MVP Minimums:**
- SLO 99.9% para endpoints de consulta
- Latência < 30s para processamento de laudo individual
- Determinismo 100%: cache por SHA-256 + pipeline_version
- Coverage de testes ≥ 80%
- Dados exclusivamente em território brasileiro
- Logs estruturados com correlation_id
- Rate limiting: 1000 req/hora por tenant

**Segurança:**
- TLS 1.2+, AES-256/KMS em repouso
- PII mascarada em logs, input validation
- Antivírus no upload, dependências auditadas

# 6. Acceptance Criteria

**R-001**: Sistema deve processar PDF nativo de laudo laboratorial em < 30s
**R-002**: Extração de valor + unidade com precisão ≥ 98% para top-50 analitos
**R-003**: Mapeamento para LOINC com ≥ 97% de acerto nos flags vs. referência
**R-004**: Determinismo: reprocessamento idêntico gera output byte-a-byte igual
**R-005**: Auditoria completa disponível por report_id
**R-006**: Sumário em PT-BR com disclaimer de não prescrição
**R-007**: Cache por hash de conteúdo + versão de pipeline
**R-008**: Validação JSON Schema 100% dos outputs
**R-009**: Conformidade LGPD: consentimento + direito ao esquecimento
**R-010**: Faixas de referência específicas por laboratório/perfil

# 7. Test Plan

**Obrigatório para MVP:**
- **Unitários**: Cada módulo isoladamente (OCR, parsing, normalização)
- **Integração**: Fluxo completo PDF → JSON estruturado
- **Contratos**: Validação OpenAPI Schema + exemplos
- **Determinismo**: Propriedade de repetibilidade 100%
- **Regressão**: Suite contra datasets rotulados (1000+ laudos)
- **Segurança**: PII masking, input validation, SQL injection
- **Performance**: Load testing até 1000 req/hora

**Ferramentas:**
- pytest + coverage para Python
- newman/postman para contratos API
- locust para load testing

# 8. Release Plan

**Versionamento**: SemVer (X.Y.Z)
- X: breaking changes na API
- Y: novas funcionalidades compatíveis  
- Z: bug fixes

**Pipeline CI/CD:**
- Pre-commit: linting (ruff) + typing (mypy) + security (bandit)
- CI: testes + coverage + build Docker
- CD: deploy staging → validação → produção

**CHANGELOG.md**: formato Keep a Changelog (Added/Changed/Fixed/Removed)

# 9. Notes & Assumptions

Ver docs/assumptions.md para lista completa.

**Principais premissas:**
- Laudos laboratoriais seguem layout tabular padrão brasileiro
- LOINC/UCUM são terminologias aceitas pelos laboratórios
- Recomendações informativas (não prescritivas) são suficientes para MVP
- OCR de qualidade comercial (AWS Textract) disponível no Brasil