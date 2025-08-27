-- Seed 001: Basic reference data
-- Created: 2025-01-15
-- Description: Essential data for MVP operation

BEGIN;

-- ============================================================================
-- BASIC REFERENCE ORGANIZATIONS (Labs)
-- ============================================================================

-- Sample lab organizations for testing
INSERT INTO organization (id, tenant_id, name, identifier, org_type, contact_info) VALUES
(
    '11111111-1111-1111-1111-111111111111'::UUID,
    '00000000-0000-0000-0000-000000000000'::UUID, -- Default tenant for seed data
    'Laboratório Central',
    '12.345.678/0001-90',
    'laboratory',
    '{"phone": "+55 11 3333-4444", "address": "São Paulo, SP"}'::jsonb
),
(
    '22222222-2222-2222-2222-222222222222'::UUID,
    '00000000-0000-0000-0000-000000000000'::UUID,
    'Lab Diagnóstico Avançado',
    '98.765.432/0001-10',
    'laboratory',
    '{"phone": "+55 21 2222-3333", "address": "Rio de Janeiro, RJ"}'::jsonb
);

-- ============================================================================
-- COMMON LOINC MAPPINGS (TOP BRAZILIAN ANALYTES)
-- ============================================================================

INSERT INTO mapping_loinc (
    tenant_id, lab_code, lab_name, loinc_code, loinc_display, confidence
) VALUES
-- Glucose
('00000000-0000-0000-0000-000000000000'::UUID, 'GLUC', 'Glicose', '2345-7', 'Glucose [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'GLUCOSE', 'Glucose', '2345-7', 'Glucose [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'GLI', 'Gli', '2345-7', 'Glucose [Mass/volume] in Serum or Plasma', 0.95),

-- Hemoglobin
('00000000-0000-0000-0000-000000000000'::UUID, 'HB', 'Hemoglobina', '718-7', 'Hemoglobin [Mass/volume] in Blood', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'HGB', 'Hemoglobina', '718-7', 'Hemoglobin [Mass/volume] in Blood', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'HEMOGLOBINA', 'Hemoglobina', '718-7', 'Hemoglobin [Mass/volume] in Blood', 1.00),

-- Cholesterol  
('00000000-0000-0000-0000-000000000000'::UUID, 'CHOL', 'Colesterol Total', '2093-3', 'Cholesterol [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'CT', 'Colesterol Total', '2093-3', 'Cholesterol [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'COLESTEROL', 'Colesterol', '2093-3', 'Cholesterol [Mass/volume] in Serum or Plasma', 0.95),

-- Creatinine
('00000000-0000-0000-0000-000000000000'::UUID, 'CREA', 'Creatinina', '2160-0', 'Creatinine [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'CREATININA', 'Creatinina', '2160-0', 'Creatinine [Mass/volume] in Serum or Plasma', 1.00),

-- TSH
('00000000-0000-0000-0000-000000000000'::UUID, 'TSH', 'TSH', '3016-3', 'Thyrotropin [Units/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'TIREOTROPINA', 'Tireotropina', '3016-3', 'Thyrotropin [Units/volume] in Serum or Plasma', 0.90),

-- Red Blood Cell Count
('00000000-0000-0000-0000-000000000000'::UUID, 'RBC', 'Hemácias', '789-8', 'Erythrocytes [#/volume] in Blood by Automated count', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'HEMACIAS', 'Hemácias', '789-8', 'Erythrocytes [#/volume] in Blood by Automated count', 1.00),

-- White Blood Cell Count
('00000000-0000-0000-0000-000000000000'::UUID, 'WBC', 'Leucócitos', '6690-2', 'Leukocytes [#/volume] in Blood by Automated count', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'LEUCOCITOS', 'Leucócitos', '6690-2', 'Leukocytes [#/volume] in Blood by Automated count', 1.00),

-- Platelets
('00000000-0000-0000-0000-000000000000'::UUID, 'PLT', 'Plaquetas', '777-3', 'Platelets [#/volume] in Blood by Automated count', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'PLAQUETAS', 'Plaquetas', '777-3', 'Platelets [#/volume] in Blood by Automated count', 1.00),

-- Urea
('00000000-0000-0000-0000-000000000000'::UUID, 'UREA', 'Ureia', '3094-0', 'Urea nitrogen [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'UREIA', 'Ureia', '3094-0', 'Urea nitrogen [Mass/volume] in Serum or Plasma', 1.00),

-- HDL Cholesterol
('00000000-0000-0000-0000-000000000000'::UUID, 'HDL', 'HDL Colesterol', '2085-9', 'Cholesterol in HDL [Mass/volume] in Serum or Plasma', 1.00),
('00000000-0000-0000-0000-000000000000'::UUID, 'HDL-C', 'HDL-C', '2085-9', 'Cholesterol in HDL [Mass/volume] in Serum or Plasma', 1.00);

-- ============================================================================
-- COMMON REFERENCE RANGES (BRAZILIAN CONSENSUS)
-- ============================================================================

INSERT INTO rangeset (
    tenant_id, analyte_key, loinc_code, lab_org_id, 
    age_min_years, age_max_years, sex, pregnancy_status,
    ref_low, ref_high, unit_ucum, source, confidence_level
) VALUES

-- Glucose (fasting) - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'glucose_fasting', '2345-7', NULL,
 18, 150, 'all', 'all', 70, 99, 'mg/dL', 'consensus', 'high'),

-- Hemoglobin - Adult Male  
('00000000-0000-0000-0000-000000000000'::UUID, 'hemoglobin', '718-7', NULL,
 18, 150, 'male', 'not_applicable', 13.5, 17.5, 'g/dL', 'consensus', 'high'),

-- Hemoglobin - Adult Female Non-pregnant
('00000000-0000-0000-0000-000000000000'::UUID, 'hemoglobin', '718-7', NULL,
 18, 150, 'female', 'not_pregnant', 12.0, 15.5, 'g/dL', 'consensus', 'high'),

-- Hemoglobin - Adult Female Pregnant
('00000000-0000-0000-0000-000000000000'::UUID, 'hemoglobin', '718-7', NULL,
 18, 45, 'female', 'pregnant', 11.0, 14.0, 'g/dL', 'consensus', 'high'),

-- Total Cholesterol - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'cholesterol_total', '2093-3', NULL,
 18, 150, 'all', 'all', 0, 200, 'mg/dL', 'consensus', 'high'),

-- Creatinine - Adult Male
('00000000-0000-0000-0000-000000000000'::UUID, 'creatinine', '2160-0', NULL,
 18, 150, 'male', 'not_applicable', 0.7, 1.3, 'mg/dL', 'consensus', 'high'),

-- Creatinine - Adult Female
('00000000-0000-0000-0000-000000000000'::UUID, 'creatinine', '2160-0', NULL,
 18, 150, 'female', 'all', 0.6, 1.1, 'mg/dL', 'consensus', 'high'),

-- TSH - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'tsh', '3016-3', NULL,
 18, 150, 'all', 'all', 0.4, 4.0, 'mIU/L', 'consensus', 'high'),

-- RBC - Adult Male
('00000000-0000-0000-0000-000000000000'::UUID, 'rbc', '789-8', NULL,
 18, 150, 'male', 'not_applicable', 4.5, 5.9, '10*6/uL', 'consensus', 'high'),

-- RBC - Adult Female  
('00000000-0000-0000-0000-000000000000'::UUID, 'rbc', '789-8', NULL,
 18, 150, 'female', 'all', 4.1, 5.1, '10*6/uL', 'consensus', 'high'),

-- WBC - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'wbc', '6690-2', NULL,
 18, 150, 'all', 'all', 4000, 11000, '/uL', 'consensus', 'high'),

-- Platelets - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'platelets', '777-3', NULL,
 18, 150, 'all', 'all', 150000, 450000, '/uL', 'consensus', 'high'),

-- Urea - Adult
('00000000-0000-0000-0000-000000000000'::UUID, 'urea', '3094-0', NULL,
 18, 150, 'all', 'all', 10, 50, 'mg/dL', 'consensus', 'high'),

-- HDL Cholesterol - Adult Male
('00000000-0000-0000-0000-000000000000'::UUID, 'hdl_cholesterol', '2085-9', NULL,
 18, 150, 'male', 'not_applicable', 40, 999, 'mg/dL', 'consensus', 'high'),

-- HDL Cholesterol - Adult Female
('00000000-0000-0000-0000-000000000000'::UUID, 'hdl_cholesterol', '2085-9', NULL,
 18, 150, 'female', 'all', 50, 999, 'mg/dL', 'consensus', 'high');

COMMIT;