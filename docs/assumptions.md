# Assumptions Register

## Technical Assumptions

- **A1**: OCR de qualidade comercial (AWS Textract/Google Document AI) disponível com latência aceitável no Brasil (owner: context_manager, date: 2025-01-15, risk: medium)
- **A2**: Layouts de laudos laboratoriais brasileiros seguem padrões tabulares identificáveis por heurísticas (owner: expert_developer, date: 2025-01-15, risk: high)
- **A3**: LOINC como terminologia padrão é aceita e mapeável para analitos brasileiros (owner: specification_agent, date: 2025-01-15, risk: medium)
- **A4**: PostgreSQL com row-level security é suficiente para segregação multi-tenant (owner: database_architect, date: 2025-01-15, risk: low)

## Business Assumptions

- **A5**: Recomendações informativas (não prescritivas) atendem necessidade de valor inicial do MVP (owner: context_manager, date: 2025-01-15, risk: medium)
- **A6**: Laboratórios fornecem faixas de referência estruturadas ou permitem configuração manual (owner: expert_developer, date: 2025-01-15, risk: high)
- **A7**: Determinismo absoluto é mandatório mesmo com redução de flexibilidade de IA (owner: context_manager, date: 2025-01-15, risk: low)

## Regulatory Assumptions

- **A8**: Escopo informativo (não diagnóstico) dispensa classificação como SaMD no Brasil (owner: context_manager, date: 2025-01-15, risk: high)
- **A9**: LGPD compliance via consentimento + minimização + território brasileiro é suficiente (owner: context_manager, date: 2025-01-15, risk: medium)
- **A10**: Armazenamento em nuvem brasileira atende requisitos de residência de dados (owner: expert_developer, date: 2025-01-15, risk: low)

## Integration Assumptions

- **A11**: FHIR R4 facade é suficiente para interoperabilidade inicial, sem necessidade de HL7 v2 no MVP (owner: api_architect, date: 2025-01-15, risk: low)
- **A12**: S3-compatible storage no Brasil tem performance adequada para artefatos OCR (owner: expert_developer, date: 2025-01-15, risk: low)

## How to resolve an assumption

### High Risk (A2, A6, A8)
1. **A2 (Layouts)**: Coletar 100+ laudos de 10+ laboratórios diferentes, criar dataset de validação
2. **A6 (Faixas)**: Entrevistar 5+ laboratórios sobre disponibilidade de faixas estruturadas
3. **A8 (SaMD)**: Consultar advogado especialista em regulação médica para confirmação

### Medium Risk (A1, A3, A5, A9)
1. **A1 (OCR)**: Implementar POC com serviços disponíveis, medir latência real
2. **A3 (LOINC)**: Mapear top-100 analitos brasileiros para LOINC, validar com especialistas
3. **A5 (Valor)**: Entrevistar 3+ potenciais clientes sobre aceitação de escopo informativo
4. **A9 (LGPD)**: Revisão com advogado de privacidade sobre implementação

### Low Risk (A4, A7, A10, A11, A12)
- Validar durante implementação, sem ação prévia necessária