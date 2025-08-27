# API de Extração e Normalização de Exames Clínicos

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.108.0-009639.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg?style=flat&logo=postgresql)](https://www.postgresql.org)

API determinística para ingestão de laudos de exames (PDF/imagem), extração OCR, normalização LOINC/UCUM, cálculo de flags e geração de recomendações informativas para o contexto brasileiro.

## 🎯 Principais Características

- **Determinismo**: Mesmo input → mesmo output (cache por hash)
- **Auditabilidade**: Trilha completa de processamento
- **Interoperabilidade**: LOINC, UCUM, SNOMED CT
- **Conformidade LGPD**: Dados em território brasileiro, consentimento, minimização
- **Multi-tenant**: Isolamento seguro de dados por tenant
- **Escalabilidade**: Processamento paralelo via workers

## 📋 Especificação

Para detalhes completos da especificação técnica, consulte:
- [docs/system_spec.md](docs/system_spec.md) - Especificação do sistema
- [docs/assumptions.md](docs/assumptions.md) - Premissas e riscos
- [docs/traceability.csv](docs/traceability.csv) - Rastreabilidade de requisitos

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Docker & Docker Compose
- Make

### Setup Completo (Recomendado)

```bash
# Clone e configure o ambiente completo
git clone <repository-url>
cd API-Analysa-2

# Setup automático com Docker
make dev-setup
```

Este comando irá:
1. Criar ambiente virtual Python
2. Instalar dependências
3. Iniciar serviços Docker (PostgreSQL, Redis, MinIO)
4. Executar migrações de banco
5. Carregar dados de seed

### Acesso aos Serviços

- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/minioadmin123)

### Autenticação para Desenvolvimento

Use tokens de desenvolvimento pré-configurados:

```bash
# Admin completo
curl -H "Authorization: Bearer dev-admin" http://localhost:8000/v1/admin/rangesets

# Usuário regular
curl -H "Authorization: Bearer dev-user" http://localhost:8000/v1/ingestions

# Somente leitura
curl -H "Authorization: Bearer dev-read" http://localhost:8000/v1/reports/123
```

## 🛠️ Desenvolvimento

### Comandos Úteis

```bash
# Executar aplicação localmente
make run

# Executar testes
make test

# Verificações de qualidade
make dev  # lint + type + test

# Logs do Docker
make docker-logs

# Parar serviços
make docker-down
```

### Estrutura do Projeto

```
📦 API-Analysa-2
├── 📁 src/                    # Código fonte da aplicação
│   ├── 📁 api/v1/            # Endpoints da API REST
│   ├── 📁 core/              # Configurações e exceções
│   ├── 📁 db/                # Conexão de banco
│   ├── 📁 models/            # Modelos SQLAlchemy
│   ├── 📁 schemas/           # Schemas Pydantic
│   ├── 📁 services/          # Lógica de negócio
│   └── 📄 main.py            # Entry point da aplicação
├── 📁 tests/                 # Testes automatizados
├── 📁 db/                    # Migrações e seeds
├── 📁 api/                   # Especificação OpenAPI
├── 📁 docs/                  # Documentação do sistema
└── 📄 docker-compose.yml    # Orquestração local
```

## 📊 Pipeline de Processamento

1. **Ingestão**: Upload de PDF/imagem via API
2. **OCR**: Extração de texto com AWS Textract/Tesseract
3. **Parsing**: Detecção de tabelas e estruturas
4. **Extração**: NER para analitos, valores, unidades
5. **Normalização**: Mapeamento LOINC/UCUM
6. **Flags**: Comparação com faixas de referência
7. **Sumário**: Geração de recomendações informativas

## 🔧 Configuração

### Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
# Banco de dados
DATABASE_URL=postgresql://user:pass@localhost:5432/clinical_db

# AWS para OCR e Storage
AWS_REGION=us-east-1
S3_BUCKET_NAME=clinical-extraction-bucket

# Autenticação OAuth2/OIDC
OAUTH2_TOKEN_URL=https://auth.provider.com/oauth/token
OAUTH2_AUDIENCE=clinical-extraction-api
```

### Banco de Dados

```bash
# Executar migrações
make migrate

# Carregar dados de referência
make seed
```

## 🧪 Testes

```bash
# Todos os testes
make test

# Apenas testes de contrato da API
pytest tests/test_api_contracts.py

# Testes com coverage
pytest --cov=src --cov-report=html
```

### Tipos de Teste

- **Unitários**: Módulos isolados
- **Integração**: Fluxo completo
- **Contratos**: Validação OpenAPI
- **Determinismo**: Propriedade de repetibilidade

## 📈 Monitoramento

### Health Check

```bash
curl http://localhost:8000/health
```

### Métricas

- Latência por fase do pipeline
- Taxa de erro por endpoint
- Confiança de mapeamento LOINC
- Cache hit ratio

## 🔐 Segurança

### LGPD Compliance

- ✅ Consentimento explícito
- ✅ Minimização de dados
- ✅ Direito ao esquecimento
- ✅ Portabilidade de dados
- ✅ Auditoria completa

### Multi-tenancy

- Row-Level Security (RLS) no PostgreSQL
- Isolamento completo de dados por tenant
- Auditoria por tenant

## 🚀 Deploy

### Produção

1. Configure variáveis de ambiente de produção
2. Use banco PostgreSQL gerenciado
3. Configure AWS S3 brasileiro
4. Setup OAuth2/OIDC provider
5. Configure monitoramento

### Docker

```bash
# Build de produção
docker build -t clinical-extraction-api .

# Deploy com compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 API Endpoints

### Principais Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/v1/ingestions` | Criar ingestão de documento |
| `GET` | `/v1/ingestions/{id}` | Status da ingestão |
| `GET` | `/v1/reports/{id}` | Laudo estruturado |
| `GET` | `/v1/patients/{id}/observations` | Observações do paciente |
| `POST` | `/v1/admin/rangesets` | Configurar faixas de referência |

### Exemplos

```bash
# Criar ingestão
curl -X POST "http://localhost:8000/v1/ingestions" \
  -H "Authorization: Bearer dev-user" \
  -H "Content-Type: application/json" \
  -d '{"document_type": "laboratory_report", "filename": "laudo.pdf"}'

# Obter laudo estruturado
curl -H "Authorization: Bearer dev-user" \
  "http://localhost:8000/v1/reports/123e4567-e89b-12d3-a456-426614174000"
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie branch feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra Pull Request

### Padrões de Código

- **Linting**: Ruff para formatação e style
- **Tipos**: MyPy para type checking
- **Segurança**: Bandit para análise de segurança
- **Testes**: Pytest com coverage ≥ 80%

## 📄 Licença

Este projeto é proprietário. Todos os direitos reservados.

## 🆘 Suporte

- **Documentação**: [/docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Contato**: api-support@clinical-extraction.com

---

**Nota**: Este material é informativo e não substitui avaliação médica profissional.