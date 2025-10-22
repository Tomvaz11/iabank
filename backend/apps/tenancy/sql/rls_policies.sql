CREATE SCHEMA IF NOT EXISTS iabank;

CREATE OR REPLACE FUNCTION iabank.apply_tenant_rls_policies()
RETURNS void AS $$
BEGIN
    PERFORM 1;
    EXECUTE 'ALTER TABLE tenant_theme_tokens ENABLE ROW LEVEL SECURITY';
    EXECUTE 'CREATE POLICY IF NOT EXISTS tenant_theme_tokens_isolation ON tenant_theme_tokens USING (tenant_id::text = current_setting(''iabank.current_tenant_id'', true))';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION iabank.revert_tenant_rls_policies()
RETURNS void AS $$
BEGIN
    PERFORM 1;
    EXECUTE 'DROP POLICY IF EXISTS tenant_theme_tokens_isolation ON tenant_theme_tokens';
    EXECUTE 'ALTER TABLE tenant_theme_tokens DISABLE ROW LEVEL SECURITY';
END;
$$ LANGUAGE plpgsql;
