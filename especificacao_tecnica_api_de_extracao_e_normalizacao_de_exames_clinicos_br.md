# Especificação Técnica — API de Extração, Normalização e Recomendações de Exames Clínicos (Brasil)

> **Objetivo**: construir uma API determinística e auditável que ingere laudos de exames (laboratoriais e de imagem), extrai e normaliza biomarcadores, verifica faixas de referência específicas por laboratório/paciente, gera visualizações e produz recomendações **informativas** (não prescritivas), adequadas ao contexto brasileiro e integráveis via FHIR/HL7.

---

## 1) Escopo e Visão

**Escopo (P0—P2)**
- **P0 (MVP)**: PDF/Imagem de laudos laboratoriais (hemograma, bioquímica, urina, etc.), com OCR, extração de valores/unidades/faixas de referência, normalização para LOINC/UCUM, cálculo de flags (baixo/normal/alto), visualizações de biomarcadores e sumário textual determinístico; recomendações informativas baseadas em regras clínicas de baixo risco.
- **P1**: Ingestão interoperável (HL7 v2 ORU^R01, FHIR R4/BR Core), importação por SFTP/Direct-Connect, portal de configurações de faixas por laboratório, feedback de profissionais de saúde.
- **P2**: Radiologia: ingestão de **DICOM SR** e laudos textuais (PDF/TXT), extração de medidas, achados e conclusões, mapeamento para **LOINC/SNOMED CT**; suporte a séries temporais e comparativos entre exames.

**Fora do escopo (por ora)**
- Diagnóstico automatizado ou tomada de decisão clínica prescritiva (classificação como **SaMD** exigiria outro escopo regulatório).
- Interpretação de imagem pixel-a-pixel (CAD/IA diagnóstica).

**Público-alvo**: clínicas/laboratórios, prontuários eletrônicos (PEP/EMR), healthtechs, operadoras.

---

## 2) Requisitos

### 2.1 Funcionais
1. **Ingestão de documentos**: upload de PDF/JPEG/PNG; recepção de HL7 v2 (ORU^R01) e FHIR (DiagnosticReport, Observation) no P1.
2. **OCR e Extração Estruturada**: detecção de tabelas, valores, unidades, métodos, faixas de referência e observações.
3. **Normalização**: mapeamento para **LOINC** (biomarcadores), **UCUM** (unidades), **SNOMED CT** (achados/qualificadores), CID-10 (diagnósticos, se fornecidos).
4. **Perfil do paciente**: idade, sexo, gestação, condições relevantes (quando informadas) para seleção de faixas.
5. **Regras e Flags**: comparação com faixas por laboratório e/ou guidelines; geração de **status** (L, N, H), delta vs. exame anterior, significância clínica.
6. **Resumo e Recomendações**: geração textual determinística com linguagem segura ("para discussão com seu médico"), evidências e limites de escopo.
7. **Visualização**: endpoints para gráficos de tendência, comparação vs. referência, percentis.
8. **Versionamento & Determinismo**: mesma entrada → mesmo output (vide seção 6); **cache** por hash de conteúdo e ID de pipeline.
9. **Auditoria**: trilha completa (documento original, versões de modelos/regras, prompts, outputs, validações, decisões).
10. **Admin/Config**: cadastro de faixas por laboratório, mapeamentos LOINC, transformações de unidade.

### 2.2 Não Funcionais
- **LGPD-first**: consentimento, minimização de dados, portabilidade, deleção sob solicitação, dados em território brasileiro.
- **Segurança**: criptografia em trânsito (TLS 1.2+), em repouso (AES-256/KMS), RBAC/ABAC, segregação por tenant, antivírus/antimalware no upload.
- **Confiabilidade**: SLO 99.9% API, filas idempotentes, DLQs, reprocessamento.
- **Observabilidade**: logs estruturados, métricas (extração, latência, acurácia), traces.
- **Escalabilidade**: processamento paralelo via workers, auto-scaling.
- **Testabilidade**: datasets rotulados, testes de regressão e contratos (FHIR/HL7), validação clínica por SME.

---

## 3) Arquitetura (Visão Geral)

**Camadas**
- **Gateway/API** → **Ingestão** → **OCR/Parsing** → **NLP/Extração** → **Normalização & Validação** → **Regras/Resumo** → **Persistência** → **Visualização/Relato**.

**Componentes**
- API Gateway (rate-limit, auth OIDC/OAuth2).
- Ingestion Service (Upload, HL7/FHIR listeners, SFTP watchers).
- OCR Service (PDF/Image OCR + table detection).
- Parser Service (layout, seções, tabelas; heurísticas determinísticas).
- NLP Extractor (NER + Pattern Mining + LLM *constrained* quando necessário).
- Normalizer (LOINC, UCUM, SNOMED; unidades e faixas por perfil).
- Rules Engine (flags, deltas, interpretação segura).
- Summary Generator (template + LLM com **grammar-constrained decoding**).
- Data Services (FHIR façade; storage de objetos; DB relacional; vetor semântico para grounding).
- Admin Console (mapeamentos, faixas, monitoramento de qualidade).

**Infra**: Kubernetes (K8s) + Istio/Linkerd, filas (Kafka/RabbitMQ), armazenamento de objetos (S3-compatível no Brasil), Postgres, Redis, Vault/KMS, OpenTelemetry.

---

## 4) Padrões e Interoperabilidade
- **FHIR R4 (HL7 Brasil / BR Core)**: `Patient`, `Observation`, `DiagnosticReport`, `Specimen`, `Organization`, `Encounter`.
- **HL7 v2 ORU^R01**: adaptadores para ingestão legada.
- **Terminologias**: **LOINC** (laboratório), **UCUM** (unidades), **SNOMED CT** (achados/qualificadores), **CID-10**.
- **Identificadores**: `system`/`code` consistentes; mapeamento custom por laboratório.

---

## 5) Modelo de Dados (interno)

**Tabelas principais** (PostgreSQL)
- `document`: `id`, `tenant_id`, `sha256`, `mime_type`, `ingest_source`, `status`, `created_at`.
- `extraction_job`: `id`, `document_id`, `pipeline_version`, `started_at`, `ended_at`, `status`, `hash_config`.
- `patient`: `id`, `tenant_id`, `external_id`, `name`, `dob`, `sex`, `pregnancy_status`, `metadata`.
- `lab_test` (Observação normalizada): `id`, `patient_id`, `loinc_code`, `analyte_display`, `value_num`, `value_text`, `unit_ucum`, `ref_low`, `ref_high`, `ref_text`, `flag`, `collected_at`, `resulted_at`, `performer_org_id`, `raw_json`.
- `report` (DiagnosticReport): `id`, `patient_id`, `category` (lab/imaging), `conclusion_text`, `status`, `issued_at`, `raw_json`.
- `rangeset` (faixas por lab/profile): `id`, `analyte_key`, `loinc_code`, `lab_org_id`, `stratifiers` (idade/sexo/gestação/metodologia), `ref_low`, `ref_high`, `unit_ucum`, `source`, `effective_period`.
- `mapping_loinc`: `id`, `tenant_id`, `lab_code`, `loinc_code`, `confidence`, `rules`.
- `audit_event`: imutável/append-only (quem/como/quando).

**Armazenamento de objetos**
- Original + artefatos (OCR JSON, page images, DICOM SR XML/JSON, prompts, outputs) em bucket S3-compatível com versionamento.

---

## 6) Determinismo e Reprodutibilidade (Crítico)

1. **Hash de Conteúdo**: SHA-256 do arquivo + metadados relevantes → chave de cache. Se `sha256` + `pipeline_version` + `config_hash` iguais, retorna exatamente o mesmo output.
2. **Pipelines Versionados**: `pipeline_version` inclui versões de modelos (OCR/NLP/LLM), regras, mapeamentos e templates. Qualquer alteração gera nova versão.
3. **Config imutável**: serializar configuração completa (JSON) e fixar seeds.
4. **LLM com Decodificação Constrangida**: JSON Schema/EBNF + **temperature=0**, **top_k=1** e **deterministic sampling**; uso de bibliotecas como *Outlines/Guidance/LMQL* para garantir gramática; quedas de volta para heurísticas.
5. **Post-Validação**: validar contra **JSON Schema** e regras de coerência (ex.: unidade compatível com LOINC, faixa faz sentido, valor numérico parseado).
6. **Fallbacks e Idempotência**: se LLM divergir, caminho alternativo puramente determinístico (regex+padrões); reprocessamento idempotente.
7. **Snapshots de Modelos**: artefatos de modelos (OCR/NLP) em registry com hash; não usar "latest".

---

## 7) Pipeline de Extração (Laboratoriais)

**7.1 OCR/Parsing**
- PDF nativo: extrair texto e estrutura (lályout, tabelas) com heurísticas determinísticas (ex.: `pdfminer`, `pdfplumber`, `camelot/tabula`).
- PDF imagem/scan: OCR com engine de qualidade (Textract/DocAI/Form Recognizer) + detecção de tabela; sempre guardar bounding boxes para rastreabilidade.
- Normalizar caracteres (PT-BR), casas decimais, vírgulas/pontos.

**7.2 Detecção de Linhas/Tabelas**
- Heurísticas: cabeçalho → analito | resultado | unidade | referência | método.
- Tolerância a variações (ex.: "VR", "Valores de Referência", "Intervalo", "Método").

**7.3 Extração de Itens**
- RegEx + autômatos para capturar: `analyte`, `value`, `unit`, `ref_low`, `ref_high`, `flag textual` (ex.: "*"/H/L), `method`, `sample`.
- NER custom (spaCy pt) para analitos/aliases; dicionários por laboratório; tabela de sinônimos.

**7.4 Normalização**
- Resolver `unit` → **UCUM** e converter valores (ex.: mg/dL ↔ mmol/L) via tabela de conversão oficial.
- Mapear `analyte` → **LOINC** (regra/sinônimos + contexto de unidade/metodologia). Confiabilidade registrada.
- Selecionar faixa: `rangeset` por (lab, analyte, idade, sexo, gestação, método). Fallback: faixa padrão/consenso.

**7.5 Validação**
- Regras de plausibilidade: valores fora de limites fisiológicos; checagem de unidade incompatível; parse robusto de negativos/inequações ("<", ">").
- Registro de avisos e incertezas em `raw_json`.

---

## 8) Pipeline de Radiologia (P2)

- **DICOM SR**: parsing de medidas/achados estruturados; mapeamento para LOINC/SNOMED; vincular a `DiagnosticReport`.
- **Laudos textuais**: similar ao laboratório, com NER para achados, órgãos, lateralidade, estadiamento; lista de problemas (Problem List) em SNOMED quando possível.
- **Não** processar pixels (sem CAD/IA diagnóstica) neste escopo.

---

## 9) Regras, Flags e Recomendações

**9.1 Flags**
- `flag`: `L`/`N`/`H` comparando `value_num` com `[ref_low, ref_high]`.
- **Delta**: variação percentual vs. último exame; marcar como significativa quando acima de limiar por analito.

**9.2 Regras Clínicas de Baixo Risco**
- Ex.: *TSH alto* + *T4 livre normal* → "padrão compatível com hipotireoidismo subclínico? **Para discussão com seu médico**".
- Ex.: *Ferritina baixa* + *Hb baixa* → considerar investigação de deficiência de ferro, **sem** prescrição.
- Regras mantidas em repositório (YAML/DSL) versionado, com fontes e validação por SME.

**9.3 Geração de Sumário**
- **Templates determinísticos** com *slots*; quando usar LLM, **grammar-constrained** para JSON → renderer textual.
- Idioma: PT-BR (suporte a EN futuramente).
- Tom: informativo, não prescritivo; incluir disclaimers e limites.

---

## 10) Segurança, LGPD e Conformidade

- **Base legal**: execução de contrato/consentimento; finalidade explícita; retenção mínima.
- **Consentimento & Preferências**: registrar consent status por paciente/tenant; revogação e direito ao esquecimento.
- **Criptografia**: TLS 1.2+, AES-256/KMS; segregação por tenant (schema por tenant ou row-level security).
- **Controle de Acesso**: OAuth2/OIDC (Keycloak/Auth0) + RBAC/ABAC (papéis: admin, analista, leitura).
- **Logs & Auditoria**: imutáveis, com carimbo de tempo sincr. NTP; hash encadeado por lote.
- **Residência de Dados**: hospedar em região BR (quando no cloud), backups cifrados.
- **DLP**: mascaramento de PII em logs; varredura anti-malware no upload.
- **Avaliação de Impacto (DPIA)** antes do go-live; processos de incident response.

---

## 11) APIs Externas (Contrato)

**Padrões gerais**
- REST + JSON; `content-type: application/json`; versionamento via `/v1`.
- Idempotência com `Idempotency-Key`.

**Principais Endpoints**
- `POST /v1/ingestions` — cria ingestão (upload URL pré-assinado ou multipart); retorna `document_id`.
- `POST /v1/ingestions/{id}/finalize` — sinaliza fim do upload (inicia pipeline).
- `GET /v1/ingestions/{id}` — status e artefatos.
- `GET /v1/reports/{report_id}` — JSON estruturado do laudo (inclui observations e sumário).
- `GET /v1/patients/{id}/observations` — lista normalizada (paginada, filtros: LOINC, data, flag).
- `POST /v1/admin/rangesets` — CRUD de faixas por laboratório.
- `POST /v1/admin/mappings/loinc` — cadastro/treinamento de mapeamentos.
- **FHIR façade**: `GET/POST /fhir/Observation`, `DiagnosticReport`, `Patient` (P1+).
- **Webhooks**: `POST {callback_url}` na conclusão.

**Esquema de Resposta (exemplo simplificado)**
```json
{
  "report_id": "rep_123",
  "patient": {"id":"pat_1","dob":"1980-05-12","sex":"female"},
  "observations": [
    {
      "loinc": "2345-7",
      "display": "Glucose [Mass/volume] in Serum or Plasma",
      "value_num": 102.0,
      "unit_ucum": "mg/dL",
      "ref_low": 70.0,
      "ref_high": 99.0,
      "flag": "H",
      "collected_at": "2025-08-12T09:30:00-03:00"
    }
  ],
  "summary": {
    "text": "Sua glicose está levemente acima do intervalo de referência do laboratório...",
    "recommendations": [
      {"code":"GLUCOSE_ELEVATED_MILD","text":"Discuta com seu médico..."}
    ],
    "disclaimer": "Este material é informativo e não substitui avaliação médica."
  },
  "provenance": {
    "pipeline_version": "p0.7.3",
    "sha256": "...",
    "artifacts": ["s3://.../ocr.json","s3://.../layout.json"]
  }
}
```

---

## 12) Tecnologias Recomendadas

- **OCR/Doc AI**: AWS Textract, Google Document AI, Azure Form Recognizer (avaliar custo/latência/latim). Alternativa OSS: `Tesseract` (com tuning) + `LayoutParser`.
- **Parsing PDF**: `pdfplumber`, `pdfminer.six`, `camelot`/`tabula`.
- **NLP (PT-BR)**: spaCy pt + modelos custom; Stanza; regras com `regex`/`flashtext`/`aho-corasick`.
- **LLM**: modelo hospedado e **pinnado** (ex.: open-source fine-tuned) com **grammar-constrained decoding** (Outlines/Guidance/LMQL). Evitar serviços com nondeterminismo não controlável.
- **Terminologias**: LOINC, UCUM, SNOMED CT (licenciamento necessário), CID-10.
- **Regras**: `durable_rules` (Python), Open Policy Agent (OPA) para políticas; repositório YAML versionado.
- **Infra**: K8s, Terraform, Helm, ArgoCD/GitOps, Postgres, Redis, S3, Kafka/RabbitMQ, Vault.
- **Observabilidade**: OpenTelemetry, Prometheus, Grafana, Loki.
- **MLOps**: MLflow/Weights&Biases para versionar modelos; DVC para datasets; Label Studio para anotação.

---

## 13) Qualidade, Métricas e Validação Clínica

- **KPIs de Extração**: precisão/recall por campo (valor, unidade, faixa, LOINC), acurácia global de mapeamento (>98% para top analitos), taxa de fallbacks.
- **KPIs de Normalização**: conversões UCUM corretas, consistência de faixas.
- **KPIs de Recomendações**: cobertura de regras, taxa de discordância com revisões clínicas.
- **Datasets**: amostra estratificada por laboratório/layout, incluindo casos difíceis (tabelas multi-linha, símbolos, desigualdades, pediatria/gestação).
- **Revisão Clínica**: painel de especialistas para aprovar regras e phrasing.
- **Testes**: unitários, integração (contratos FHIR/HL7), regressão de OCR/NLP, propriedade determinística (repetibilidade 100%).

---

## 14) Observabilidade & Auditoria

- **Tracing** por documento com `trace_id` propagado.
- **Métricas**: latência por fase, taxa de erro, confiança do mapeamento LOINC, diffs entre versões.
- **Dashboards**: qualidade por tenant, trends de acurácia, SLA, custos.
- **Auditoria**: log de decisões (qual regra acionou, por quê), versões de modelos/templates, hashes.

---

## 15) UX de Visualização (para clientes que consumirem a API)

- **Cards por biomarcador**: valor atual, faixa, flag, variação desde último exame.
- **Gráfico de tendência**: séries por analito; marcações de mudanças de método/lab.
- **Contexto**: faixa dinâmica conforme perfil; tooltip com UCUM/LOINC e fonte de faixa.
- **Export**: PDF/JSON do sumário; link de evidências.

---

## 16) Roadmap & Marcos

**P0 (8–12 semanas)**
1. Fundações (K8s, Postgres, S3, Auth, Observabilidade, Auditoria).
2. Pipeline Lab PDF (OCR/Parsing/Extração/Normalização/Flags).
3. Admin de faixas e mapeamentos LOINC.
4. Sumário determinístico com templates + grammar-constrained LLM.
5. Visualização básica (gráficos via API) e FHIR read-only.
6. Conjunto de testes + validação clínica inicial.

**P1 (8–10 semanas)**
1. Ingestão HL7 v2 e FHIR write.
2. Portal de QA/rotulagem e feedback de médicos.
3. Regras clínicas ampliadas (baixo risco) e delta longitudinal.
4. Ferramentas de monitoramento de qualidade (KPIs, drift, custo/OCR).

**P2 (10–14 semanas)**
1. Radiologia DICOM SR + laudo textual.
2. Faixas avançadas (pediatria/gestação/metodologia específica).
3. Internacionalização (EN), multi-tenant avançado, RBAC fino.

---

## 17) Riscos e Mitigações

- **Nondeterminismo de LLM** → grammar-constrained + seeds + fallback determinístico; snapshot de modelos.
- **Variedade de layouts** → heurísticas robustas + dicionários por laboratório + aprendizagem contínua com QA.
- **Faixas divergentes** → fonte única por lab + período de vigência + versionamento.
- **Unidades inconsistentes** → UCUM + validação de conversão + alerta de ambiguidade.
- **Compliance/licenças** → gestão de terminologias (SNOMED/LOINC), LGPD, contratos com provedores.

---

## 18) Critérios de Aceite (P0)

- Reprocessamento idêntico (mesmo input/config) → **output byte a byte idêntico**.
- ≥ 98% de precisão na extração de **valor** e **unidade** nos top-50 analitos.
- ≥ 97% de acerto de **flag** vs. referência do laboratório.
- 100% dos outputs válidos contra JSON Schema.
- Auditoria completa disponível por `report_id`.

---

## 19) Exemplo de JSON Schema (observations)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/schemas/observation.json",
  "type": "object",
  "required": ["loinc", "display", "value_num", "unit_ucum", "ref_low", "ref_high", "flag"],
  "properties": {
    "loinc": {"type":"string", "pattern":"^[0-9]+-[0-9]$"},
    "display": {"type":"string"},
    "value_num": {"type":"number"},
    "value_text": {"type":["string","null"]},
    "unit_ucum": {"type":"string"},
    "ref_low": {"type":"number"},
    "ref_high": {"type":"number"},
    "flag": {"type":"string", "enum":["L","N","H"]},
    "collected_at": {"type":"string","format":"date-time"}
  }
}
```

---

## 20) Pseudocódigo do Render de Sumário Determinístico

```python
# input: observations[], patient_profile, rules_engine
highlights = []
for obs in observations:
    if obs.flag != 'N':
        highlights.append(obs)

highlights.sort(key=lambda x: abs((x.value_num - x.ref_high) if x.flag=='H' else (x.ref_low - x.value_num)), reverse=True)

sections = []
for h in highlights[:5]:
    recs = rules_engine.get_recommendations(h, patient_profile)
    sections.append({
        "title": f"{h.display}",
        "body": f"Valor {h.value_num} {h.unit_ucum} ({h.flag}); referência {h.ref_low}-{h.ref_high}.",
        "recs": recs
    })

summary = template_engine.render({
    "patient": patient_profile,
    "sections": sections,
    "disclaimer": DISCLAIMER
})
```

---

## 21) Próximos Passos Imediatos

1. Definir provedores (OCR/Cloud) e requisitos de residência de dados no Brasil.
2. Criar dicionário inicial de mapeamento LOINC para top-200 analitos brasileiros (sinônimos PT-BR).
3. Implementar `pipeline_version` + `config_hash` + cache determinístico.
4. Construir dataset de 1.000 laudos (diversos labs) para QA.
5. Especificar `JSON Schema` final e contrato de APIs; iniciar desenvolvimento P0.

---

**Notas**
- Todo conteúdo é informativo e destina-se a apoiar, não substituir, a relação entre paciente e profissional de saúde.
- Licenças de terminologias (SNOMED, LOINC) e conformidade com LGPD são mandatórias antes do go-live.

