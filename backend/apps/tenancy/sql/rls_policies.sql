CREATE SCHEMA IF NOT EXISTS iabank;

CREATE OR REPLACE FUNCTION iabank.apply_tenant_rls_policies()
RETURNS void AS $$
DECLARE
    table_name text;
    tables text[] := ARRAY[
        'tenant_theme_tokens',
        'banking_customer',
        'banking_address',
        'banking_consultant',
        'banking_bank_account',
        'banking_account_category',
        'banking_supplier',
        'banking_loan',
        'banking_installment',
        'banking_financial_transaction',
        'banking_credit_limit',
        'banking_contract',
        'tenancy_seed_profile',
        'tenancy_seed_run',
        'tenancy_seed_batch',
        'tenancy_seed_checkpoint',
        'tenancy_seed_queue',
        'tenancy_seed_dataset',
        'tenancy_seed_idempotency',
        'tenancy_seed_rbac',
        'tenancy_seed_budget_ratelimit',
        'tenancy_seed_evidence'
    ];
BEGIN
    PERFORM 1;

    FOREACH table_name IN ARRAY tables LOOP
        IF to_regclass('public.' || table_name) IS NULL THEN
            CONTINUE;
        END IF;

        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
        IF NOT EXISTS (
            SELECT 1
            FROM pg_policies
            WHERE schemaname = 'public'
              AND tablename = table_name
              AND policyname = format('%s_isolation', table_name)
        ) THEN
            EXECUTE format(
                'CREATE POLICY %s_isolation ON %I USING (tenant_id::text = current_setting(''iabank.current_tenant_id'', true))',
                table_name,
                table_name
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION iabank.revert_tenant_rls_policies()
RETURNS void AS $$
DECLARE
    table_name text;
    tables text[] := ARRAY[
        'tenant_theme_tokens',
        'banking_customer',
        'banking_address',
        'banking_consultant',
        'banking_bank_account',
        'banking_account_category',
        'banking_supplier',
        'banking_loan',
        'banking_installment',
        'banking_financial_transaction',
        'banking_credit_limit',
        'banking_contract',
        'tenancy_seed_profile',
        'tenancy_seed_run',
        'tenancy_seed_batch',
        'tenancy_seed_checkpoint',
        'tenancy_seed_queue',
        'tenancy_seed_dataset',
        'tenancy_seed_idempotency',
        'tenancy_seed_rbac',
        'tenancy_seed_budget_ratelimit',
        'tenancy_seed_evidence'
    ];
BEGIN
    PERFORM 1;
    FOREACH table_name IN ARRAY tables LOOP
        IF to_regclass('public.' || table_name) IS NULL THEN
            CONTINUE;
        END IF;

        EXECUTE format('DROP POLICY IF EXISTS %s_isolation ON %I', table_name, table_name);
        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', table_name);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
