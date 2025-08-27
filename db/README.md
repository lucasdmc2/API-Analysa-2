# Database Setup - API de Extração e Normalização de Exames Clínicos

## Architecture

PostgreSQL database with multi-tenant row-level security (RLS) for secure data isolation.

## Schema Overview

### Core Tables
- `document` - Uploaded files and metadata
- `extraction_job` - Processing pipeline runs with deterministic caching
- `patient` - Demographics and profile data (encrypted PII)
- `lab_test` - Normalized observations (LOINC/UCUM)
- `report` - Diagnostic reports with AI-generated summaries
- `rangeset` - Reference ranges by lab/patient profile
- `mapping_loinc` - Lab code to LOINC mappings
- `organization` - Labs, hospitals, clinics
- `audit_event` - Immutable audit trail

### Security Features
- Row-Level Security (RLS) for tenant isolation
- Encrypted PII storage
- Complete audit trail with correlation IDs
- Deterministic caching by content hash + pipeline version

## Migration Commands

### Local Development
```bash
# Start PostgreSQL container
docker run --name clinical-db -e POSTGRES_PASSWORD=dev123 -p 5432:5432 -d postgres:15

# Apply migrations
export PGPASSWORD=dev123
psql -h localhost -U postgres -d postgres < db/migrations/001_init_core_tables.sql
psql -h localhost -U postgres -d postgres < db/migrations/002_rls_policies.sql

# Seed basic data
psql -h localhost -U postgres -d postgres < db/seed/001_basic_data.sql
```

### Production
```bash
# Use managed PostgreSQL service with proper credentials
psql $DATABASE_URL < db/migrations/001_init_core_tables.sql
psql $DATABASE_URL < db/migrations/002_rls_policies.sql
psql $DATABASE_URL < db/seed/001_basic_data.sql
```

## Usage Patterns

### Setting Tenant Context
```sql
-- Set tenant context for session (required for RLS)
SELECT set_tenant_context('your-tenant-uuid'::UUID);

-- All subsequent queries are automatically filtered by tenant
SELECT * FROM patient; -- Only returns this tenant's patients
```

### Deterministic Processing Cache
```sql
-- Check if document already processed with same pipeline version
SELECT * FROM extraction_job 
WHERE document_id = $1 
  AND pipeline_version = $2 
  AND config_hash = $3
  AND status = 'completed';
```

### Finding Reference Ranges
```sql
-- Get appropriate reference range for patient/analyte
SELECT * FROM rangeset 
WHERE analyte_key = 'glucose_fasting'
  AND (lab_org_id = $lab_id OR lab_org_id IS NULL)
  AND (age_min_years IS NULL OR age_min_years <= $patient_age)
  AND (age_max_years IS NULL OR age_max_years >= $patient_age)
  AND (sex = 'all' OR sex = $patient_sex)
  AND (pregnancy_status = 'all' OR pregnancy_status = $patient_pregnancy)
ORDER BY 
  lab_org_id IS NULL, -- Lab-specific ranges first
  confidence_level DESC
LIMIT 1;
```

## Performance Considerations

- All tenant-aware tables have indexes on `tenant_id`
- Composite indexes for common query patterns
- JSONB indexes on metadata fields
- Partitioning by tenant_id recommended for large deployments

## Backup Strategy

- Daily full backups with point-in-time recovery
- Separate backup encryption keys per tenant
- Audit logs retained for 7 years minimum (compliance)

## Monitoring

Monitor these key metrics:
- RLS policy performance impact
- Audit table growth rate  
- Cache hit ratio for extraction jobs
- Query performance on tenant-filtered data