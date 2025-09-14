-- Row-Level Security (RLS) configuration for IABANK multi-tenant isolation
-- This ensures complete data isolation between tenants at the database level

-- Enable RLS on core_tenant table (only if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'core_tenant') THEN
        ALTER TABLE core_tenant ENABLE ROW LEVEL SECURITY;

        -- Create RLS policy for core_tenant
        DROP POLICY IF EXISTS tenant_isolation_policy ON core_tenant;
        CREATE POLICY tenant_isolation_policy ON core_tenant
            USING (id = current_setting('iabank.current_tenant_id')::uuid);

        RAISE NOTICE 'RLS enabled on core_tenant table';
    ELSE
        RAISE NOTICE 'core_tenant table does not exist yet - RLS will be applied after Django migrations';
    END IF;
END
$$;

-- Create function to set tenant context
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid)
RETURNS void AS $$
BEGIN
    PERFORM set_config('iabank.current_tenant_id', tenant_uuid::text, true);
END;
$$ LANGUAGE plpgsql;

-- Create function to get current tenant context
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS uuid AS $$
BEGIN
    RETURN current_setting('iabank.current_tenant_id', true)::uuid;
EXCEPTION
    WHEN others THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create function to enable RLS on all tenant-dependent tables
-- This function will be called after each migration to ensure RLS is enabled
CREATE OR REPLACE FUNCTION enable_rls_for_tenant_tables()
RETURNS void AS $$
DECLARE
    table_record RECORD;
BEGIN
    -- Find all tables that have a tenant_id or tenant column
    FOR table_record IN
        SELECT DISTINCT t.table_name
        FROM information_schema.tables t
        JOIN information_schema.columns c ON t.table_name = c.table_name
        WHERE t.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
          AND t.table_name != 'core_tenant'
          AND t.table_name NOT LIKE 'django_%'
          AND t.table_name NOT LIKE 'auth_%'
          AND (c.column_name = 'tenant_id' OR c.column_name = 'tenant')
    LOOP
        -- Enable RLS
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_record.table_name);

        -- Create tenant isolation policy
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', table_record.table_name);

        -- Check if table has tenant_id column
        IF EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = table_record.table_name
                  AND column_name = 'tenant_id') THEN
            -- Use tenant_id column
            EXECUTE format('
                CREATE POLICY tenant_isolation_policy ON %I
                USING (tenant_id = get_current_tenant())',
                table_record.table_name
            );
        ELSE
            -- Use tenant column (foreign key)
            EXECUTE format('
                CREATE POLICY tenant_isolation_policy ON %I
                USING (tenant = get_current_tenant())',
                table_record.table_name
            );
        END IF;

        RAISE NOTICE 'RLS enabled for table: %', table_record.table_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions for the application user
GRANT EXECUTE ON FUNCTION set_tenant_context(uuid) TO PUBLIC;
GRANT EXECUTE ON FUNCTION get_current_tenant() TO PUBLIC;
GRANT EXECUTE ON FUNCTION enable_rls_for_tenant_tables() TO PUBLIC;

-- Create a role for bypassing RLS (for admin operations)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'iabank_admin') THEN
        CREATE ROLE iabank_admin;
    END IF;
END
$$;

-- Grant bypassrls to admin role
ALTER ROLE iabank_admin BYPASSRLS;

RAISE NOTICE 'Row-Level Security configured successfully for IABANK multi-tenant architecture';
RAISE NOTICE 'Use set_tenant_context(tenant_uuid) to set the current tenant context';
RAISE NOTICE 'Use get_current_tenant() to get the current tenant context';