-- Migration 002: Row Level Security Policies
-- Created: 2025-01-15
-- Description: Multi-tenant RLS policies for secure data isolation

BEGIN;

-- ============================================================================
-- TENANT ISOLATION POLICIES
-- ============================================================================

-- Document policies
CREATE POLICY document_tenant_isolation ON document
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Patient policies  
CREATE POLICY patient_tenant_isolation ON patient
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Rangeset policies
CREATE POLICY rangeset_tenant_isolation ON rangeset
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- LOINC mapping policies
CREATE POLICY mapping_loinc_tenant_isolation ON mapping_loinc
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Organization policies
CREATE POLICY organization_tenant_isolation ON organization
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Audit event policies
CREATE POLICY audit_event_tenant_isolation ON audit_event
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- ============================================================================
-- HELPER FUNCTIONS FOR TENANT CONTEXT
-- ============================================================================

-- Function to set tenant context for a session
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', tenant_uuid::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant context
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant_id', TRUE)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- AUDIT TRIGGER FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    tenant_uuid UUID;
    correlation_uuid UUID;
BEGIN
    -- Get tenant context
    tenant_uuid := get_current_tenant_id();
    
    -- Generate correlation ID if not set
    correlation_uuid := COALESCE(
        current_setting('app.correlation_id', TRUE)::UUID,
        uuid_generate_v4()
    );

    -- Insert audit record
    INSERT INTO audit_event (
        tenant_id,
        event_type,
        resource_type,
        resource_id,
        actor_id,
        actor_type,
        action,
        correlation_id,
        details
    ) VALUES (
        COALESCE(tenant_uuid, '00000000-0000-0000-0000-000000000000'::UUID),
        TG_TABLE_NAME || '_' || TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        current_setting('app.current_user_id', TRUE),
        'user',
        LOWER(TG_OP),
        correlation_uuid,
        CASE TG_OP
            WHEN 'DELETE' THEN to_jsonb(OLD)
            ELSE to_jsonb(NEW)
        END
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLY AUDIT TRIGGERS TO MAIN TABLES
-- ============================================================================

CREATE TRIGGER audit_document_changes
    AFTER INSERT OR UPDATE OR DELETE ON document
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_patient_changes
    AFTER INSERT OR UPDATE OR DELETE ON patient
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_lab_test_changes
    AFTER INSERT OR UPDATE OR DELETE ON lab_test
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_report_changes
    AFTER INSERT OR UPDATE OR DELETE ON report
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_rangeset_changes
    AFTER INSERT OR UPDATE OR DELETE ON rangeset
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

COMMIT;