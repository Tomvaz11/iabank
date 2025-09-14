-- Point-in-Time Recovery (PITR) configuration for IABANK
-- This script configures PostgreSQL for continuous backup and recovery
-- Required for FR-109: Backup and Recovery compliance

-- Configure WAL archiving and retention
-- Note: These settings are also set in docker-compose.yml command
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f';
ALTER SYSTEM SET archive_timeout = '60s';
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET wal_keep_size = '1GB';

-- Configure checkpoint settings for performance
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET max_wal_size = '2GB';
ALTER SYSTEM SET min_wal_size = '1GB';

-- Configure logging for backup monitoring
ALTER SYSTEM SET log_checkpoints = 'on';
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log slow queries
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Load pg_stat_statements extension for query monitoring
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- Configure autovacuum for better performance
ALTER SYSTEM SET autovacuum_max_workers = 3;
ALTER SYSTEM SET autovacuum_naptime = '20s';

-- Create function to perform base backup
CREATE OR REPLACE FUNCTION perform_base_backup()
RETURNS text AS $$
DECLARE
    backup_label text;
    backup_dir text;
BEGIN
    -- Generate backup label with timestamp
    backup_label := 'basebackup_' || to_char(now(), 'YYYY-MM-DD_HH24-MI-SS');
    backup_dir := '/var/backups/iabank/' || backup_label;

    -- Start backup
    PERFORM pg_start_backup(backup_label, false, false);

    -- Note: In production, this would trigger external backup script
    -- For now, just record the backup start
    INSERT INTO backup_log (backup_type, backup_label, status, started_at)
    VALUES ('BASEBACKUP', backup_label, 'STARTED', now());

    RETURN backup_dir;
END;
$$ LANGUAGE plpgsql;

-- Create backup monitoring table
CREATE TABLE IF NOT EXISTS backup_log (
    id SERIAL PRIMARY KEY,
    backup_type VARCHAR(20) NOT NULL, -- 'BASEBACKUP', 'WAL_ARCHIVE'
    backup_label VARCHAR(100),
    backup_size BIGINT,
    status VARCHAR(20) NOT NULL, -- 'STARTED', 'COMPLETED', 'FAILED'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Create index for backup monitoring queries
CREATE INDEX IF NOT EXISTS idx_backup_log_started_at ON backup_log(started_at DESC);

-- Grant permissions
GRANT EXECUTE ON FUNCTION perform_base_backup() TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON backup_log TO PUBLIC;
GRANT USAGE ON SEQUENCE backup_log_id_seq TO PUBLIC;

RAISE NOTICE 'PITR configuration completed for IABANK';
RAISE NOTICE 'WAL archiving enabled with 60s timeout';
RAISE NOTICE 'Use perform_base_backup() function to create base backups';
RAISE NOTICE 'Monitor backup status in backup_log table';