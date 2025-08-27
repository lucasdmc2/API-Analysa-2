-- Migration 001: Core tables for API de Extração e Normalização de Exames Clínicos
-- Created: 2025-01-15
-- Description: Initial database schema for clinical lab data extraction and normalization

BEGIN;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas for multi-tenancy
CREATE SCHEMA IF NOT EXISTS public;

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- Document: stores uploaded files and artifacts
CREATE TABLE document (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    original_filename TEXT,
    ingest_source VARCHAR(50) NOT NULL DEFAULT 'upload', -- upload, hl7, fhir, sftp
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded', -- uploaded, processing, completed, failed
    s3_bucket VARCHAR(100),
    s3_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT document_status_check CHECK (status IN ('uploaded', 'processing', 'completed', 'failed')),
    CONSTRAINT document_sha256_check CHECK (sha256 ~ '^[a-f0-9]{64}$')
);

-- Extraction Job: tracks processing pipeline runs
CREATE TABLE extraction_job (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES document(id) ON DELETE CASCADE,
    pipeline_version VARCHAR(20) NOT NULL, -- e.g., "p0.7.3"
    config_hash VARCHAR(64) NOT NULL, -- SHA-256 of complete config
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'running', -- running, completed, failed
    error_message TEXT,
    artifacts_s3_prefix TEXT, -- S3 path prefix for OCR outputs, etc
    cache_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT extraction_job_status_check CHECK (status IN ('running', 'completed', 'failed'))
);

-- Patient: demographic and profile data
CREATE TABLE patient (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    external_id VARCHAR(100), -- External patient ID from EMR
    name_encrypted TEXT, -- PII encrypted
    date_of_birth DATE,
    sex VARCHAR(10), -- male, female, other, unknown
    pregnancy_status VARCHAR(20), -- not_pregnant, pregnant, unknown, not_applicable
    weight_kg DECIMAL(5,2),
    height_cm DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT patient_sex_check CHECK (sex IN ('male', 'female', 'other', 'unknown')),
    CONSTRAINT patient_pregnancy_check CHECK (pregnancy_status IN ('not_pregnant', 'pregnant', 'unknown', 'not_applicable'))
);

-- Lab Test: normalized observations (LOINC/UCUM)
CREATE TABLE lab_test (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patient(id),
    document_id UUID NOT NULL REFERENCES document(id),
    extraction_job_id UUID NOT NULL REFERENCES extraction_job(id),
    
    -- LOINC normalization
    loinc_code VARCHAR(10), -- e.g., "2345-7"
    analyte_display TEXT NOT NULL, -- Human readable name
    analyte_raw TEXT, -- Original text from document
    
    -- Values
    value_num DECIMAL(20,6), -- Numeric value
    value_text TEXT, -- Text value for qualitative results
    unit_ucum VARCHAR(50), -- UCUM normalized unit
    unit_raw TEXT, -- Original unit from document
    
    -- Reference ranges
    ref_low DECIMAL(20,6),
    ref_high DECIMAL(20,6),
    ref_text TEXT, -- Textual reference (e.g., "negative")
    
    -- Flags and metadata
    flag VARCHAR(5), -- L, N, H, LL, HH
    confidence_score DECIMAL(3,2), -- 0.00-1.00
    method_name TEXT,
    sample_type VARCHAR(100), -- serum, plasma, urine, etc
    
    -- Timestamps
    collected_at TIMESTAMP WITH TIME ZONE,
    resulted_at TIMESTAMP WITH TIME ZONE,
    reported_at TIMESTAMP WITH TIME ZONE,
    
    -- Organization
    performer_org_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_json JSONB, -- Full extraction details
    
    CONSTRAINT lab_test_flag_check CHECK (flag IN ('L', 'N', 'H', 'LL', 'HH')),
    CONSTRAINT lab_test_confidence_check CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CONSTRAINT lab_test_loinc_check CHECK (loinc_code IS NULL OR loinc_code ~ '^[0-9]+-[0-9]$')
);

-- Report: diagnostic reports with summary
CREATE TABLE report (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patient(id),
    document_id UUID NOT NULL REFERENCES document(id),
    extraction_job_id UUID NOT NULL REFERENCES extraction_job(id),
    
    category VARCHAR(20) NOT NULL DEFAULT 'laboratory', -- laboratory, imaging
    code VARCHAR(50), -- LOINC code for report type
    title TEXT,
    conclusion_text TEXT,
    summary_pt TEXT, -- Generated summary in Portuguese
    recommendations JSONB, -- Array of recommendation objects
    
    status VARCHAR(20) NOT NULL DEFAULT 'final', -- preliminary, final, corrected
    issued_at TIMESTAMP WITH TIME ZONE,
    effective_period_start TIMESTAMP WITH TIME ZONE,
    effective_period_end TIMESTAMP WITH TIME ZONE,
    
    performer_org_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_json JSONB,
    
    CONSTRAINT report_category_check CHECK (category IN ('laboratory', 'imaging')),
    CONSTRAINT report_status_check CHECK (status IN ('preliminary', 'final', 'corrected'))
);

-- Range Set: reference ranges by lab/profile
CREATE TABLE rangeset (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    analyte_key VARCHAR(100) NOT NULL, -- Internal key for analyte
    loinc_code VARCHAR(10), -- LOINC if mapped
    lab_org_id UUID, -- NULL = general/consensus range
    
    -- Stratifiers for range selection
    age_min_years INTEGER,
    age_max_years INTEGER,
    sex VARCHAR(10), -- male, female, all
    pregnancy_status VARCHAR(20), -- pregnant, not_pregnant, all
    method_name TEXT,
    
    -- Range values
    ref_low DECIMAL(20,6),
    ref_high DECIMAL(20,6),
    ref_text TEXT,
    unit_ucum VARCHAR(50) NOT NULL,
    
    -- Metadata
    source VARCHAR(100), -- lab, consensus, literature
    effective_start DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_end DATE,
    confidence_level VARCHAR(10) DEFAULT 'medium', -- low, medium, high
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT rangeset_sex_check CHECK (sex IN ('male', 'female', 'all')),
    CONSTRAINT rangeset_pregnancy_check CHECK (pregnancy_status IN ('pregnant', 'not_pregnant', 'all')),
    CONSTRAINT rangeset_confidence_check CHECK (confidence_level IN ('low', 'medium', 'high'))
);

-- LOINC Mapping: lab codes to LOINC
CREATE TABLE mapping_loinc (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    lab_code VARCHAR(100) NOT NULL, -- Lab's internal code
    lab_name TEXT NOT NULL, -- Lab's name for analyte
    loinc_code VARCHAR(10) NOT NULL,
    loinc_display TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL DEFAULT 1.00, -- 0.00-1.00
    method_constraint TEXT, -- If mapping depends on method
    unit_constraint VARCHAR(50), -- If mapping depends on unit
    mapping_rules JSONB, -- Additional rules for mapping
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    validated_at TIMESTAMP WITH TIME ZONE,
    validated_by VARCHAR(100),
    
    CONSTRAINT mapping_loinc_confidence_check CHECK (confidence >= 0.00 AND confidence <= 1.00),
    CONSTRAINT mapping_loinc_code_check CHECK (loinc_code ~ '^[0-9]+-[0-9]$'),
    
    UNIQUE(tenant_id, lab_code, loinc_code)
);

-- Organization: labs, hospitals, etc
CREATE TABLE organization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    name TEXT NOT NULL,
    identifier VARCHAR(100), -- CNPJ, CNES, etc
    org_type VARCHAR(50) NOT NULL, -- laboratory, hospital, clinic
    contact_info JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT organization_type_check CHECK (org_type IN ('laboratory', 'hospital', 'clinic', 'other'))
);

-- Audit Event: immutable audit trail
CREATE TABLE audit_event (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- document_uploaded, extraction_started, etc
    resource_type VARCHAR(50) NOT NULL, -- document, patient, lab_test, etc
    resource_id UUID NOT NULL,
    
    actor_id VARCHAR(100), -- User/system that triggered event
    actor_type VARCHAR(20) NOT NULL DEFAULT 'user', -- user, system, api_key
    
    event_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    correlation_id UUID, -- For tracing related events
    
    -- Event details
    action VARCHAR(50) NOT NULL, -- created, updated, deleted, accessed
    outcome VARCHAR(20) NOT NULL DEFAULT 'success', -- success, failure
    details JSONB,
    
    -- Security
    ip_address INET,
    user_agent TEXT,
    
    CONSTRAINT audit_event_actor_type_check CHECK (actor_type IN ('user', 'system', 'api_key')),
    CONSTRAINT audit_event_outcome_check CHECK (outcome IN ('success', 'failure'))
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Document indexes
CREATE INDEX idx_document_tenant_id ON document(tenant_id);
CREATE INDEX idx_document_sha256 ON document(sha256);
CREATE INDEX idx_document_status ON document(status);
CREATE UNIQUE INDEX idx_document_tenant_sha256 ON document(tenant_id, sha256);

-- Extraction job indexes
CREATE INDEX idx_extraction_job_document_id ON extraction_job(document_id);
CREATE INDEX idx_extraction_job_status ON extraction_job(status);
CREATE INDEX idx_extraction_job_pipeline_version ON extraction_job(pipeline_version);
CREATE UNIQUE INDEX idx_extraction_job_cache ON extraction_job(document_id, pipeline_version, config_hash);

-- Patient indexes
CREATE INDEX idx_patient_tenant_id ON patient(tenant_id);
CREATE INDEX idx_patient_external_id ON patient(tenant_id, external_id);

-- Lab test indexes  
CREATE INDEX idx_lab_test_patient_id ON lab_test(patient_id);
CREATE INDEX idx_lab_test_document_id ON lab_test(document_id);
CREATE INDEX idx_lab_test_loinc_code ON lab_test(loinc_code);
CREATE INDEX idx_lab_test_collected_at ON lab_test(collected_at);
CREATE INDEX idx_lab_test_analyte_display ON lab_test(analyte_display);

-- Report indexes
CREATE INDEX idx_report_patient_id ON report(patient_id);
CREATE INDEX idx_report_document_id ON report(document_id);
CREATE INDEX idx_report_issued_at ON report(issued_at);

-- Rangeset indexes
CREATE INDEX idx_rangeset_tenant_id ON rangeset(tenant_id);
CREATE INDEX idx_rangeset_analyte_key ON rangeset(analyte_key);
CREATE INDEX idx_rangeset_loinc_code ON rangeset(loinc_code);
CREATE INDEX idx_rangeset_lab_org_id ON rangeset(lab_org_id);

-- LOINC mapping indexes
CREATE INDEX idx_mapping_loinc_tenant_id ON mapping_loinc(tenant_id);
CREATE INDEX idx_mapping_loinc_lab_code ON mapping_loinc(tenant_id, lab_code);
CREATE INDEX idx_mapping_loinc_code ON mapping_loinc(loinc_code);

-- Organization indexes
CREATE INDEX idx_organization_tenant_id ON organization(tenant_id);
CREATE INDEX idx_organization_identifier ON organization(identifier);

-- Audit indexes
CREATE INDEX idx_audit_event_tenant_id ON audit_event(tenant_id);
CREATE INDEX idx_audit_event_resource ON audit_event(resource_type, resource_id);
CREATE INDEX idx_audit_event_time ON audit_event(event_time);
CREATE INDEX idx_audit_event_correlation_id ON audit_event(correlation_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) FOR MULTI-TENANCY
-- ============================================================================

-- Enable RLS on tenant-aware tables
ALTER TABLE document ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;
ALTER TABLE rangeset ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapping_loinc ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY;

-- RLS policies will be created in a separate migration for specific tenant access

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_document_updated_at BEFORE UPDATE ON document 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patient_updated_at BEFORE UPDATE ON patient 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rangeset_updated_at BEFORE UPDATE ON rangeset 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organization_updated_at BEFORE UPDATE ON organization 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;