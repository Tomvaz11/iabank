#!/bin/bash
# IABANK Database Backup Script
# Implements FR-111: Daily backups with 30-day retention
# Implements FR-109: PITR base backup support

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/iabank"
DB_NAME="iabank"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5433"
RETENTION_DAYS=30
WAL_RETENTION_DAYS=14

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Timestamp for backup files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_DIR/backup.log"
}

# Function to perform pg_basebackup (for PITR)
perform_basebackup() {
    local backup_path="$BACKUP_DIR/basebackup_$TIMESTAMP"

    log "Starting pg_basebackup for PITR..."

    pg_basebackup \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -D "$backup_path" \
        -Ft \
        -z \
        -P \
        -W \
        --checkpoint=fast \
        --label="iabank_daily_backup_$TIMESTAMP"

    if [ $? -eq 0 ]; then
        log "✅ pg_basebackup completed successfully: $backup_path"

        # Create metadata file
        cat > "$backup_path/backup_info.json" << EOF
{
    "backup_type": "basebackup",
    "timestamp": "$TIMESTAMP",
    "database": "$DB_NAME",
    "backup_label": "iabank_daily_backup_$TIMESTAMP",
    "retention_days": $RETENTION_DAYS,
    "wal_retention_days": $WAL_RETENTION_DAYS,
    "created_at": "$(date -Iseconds)"
}
EOF

        return 0
    else
        log "❌ pg_basebackup failed"
        return 1
    fi
}

# Function to perform logical dump (as fallback)
perform_logical_dump() {
    local dump_path="$BACKUP_DIR/dump_${DB_NAME}_$TIMESTAMP.sql"

    log "Starting logical dump backup..."

    pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --no-password \
        --verbose \
        --create \
        --clean \
        --if-exists \
        --format=custom \
        --compress=9 \
        --file="$dump_path.backup"

    if [ $? -eq 0 ]; then
        log "✅ Logical dump completed successfully: $dump_path.backup"

        # Also create plain SQL dump
        pg_dump \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --no-password \
            --create \
            --clean \
            --if-exists > "$dump_path"

        # Compress plain SQL dump
        gzip "$dump_path"

        log "✅ Plain SQL dump completed: $dump_path.gz"
        return 0
    else
        log "❌ Logical dump failed"
        return 1
    fi
}

# Function to clean old backups (FR-111: 30-day retention)
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."

    # Remove old basebackups
    find "$BACKUP_DIR" -type d -name "basebackup_*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true

    # Remove old dumps
    find "$BACKUP_DIR" -type f -name "dump_*.backup" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -type f -name "dump_*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

    log "✅ Old backup cleanup completed"
}

# Function to clean old WAL files (FR-111: 14-day retention)
cleanup_old_wal() {
    local wal_archive_dir="/var/lib/postgresql/wal_archive"

    if [ -d "$wal_archive_dir" ]; then
        log "Cleaning up WAL files older than $WAL_RETENTION_DAYS days..."
        find "$wal_archive_dir" -type f -name "*.gz" -mtime +$WAL_RETENTION_DAYS -delete 2>/dev/null || true
        find "$wal_archive_dir" -type f -name "*" -mtime +$WAL_RETENTION_DAYS -delete 2>/dev/null || true
        log "✅ Old WAL cleanup completed"
    else
        log "⚠️  WAL archive directory not found: $wal_archive_dir"
    fi
}

# Function to verify backup integrity
verify_backup() {
    local backup_path="$1"

    if [ -f "$backup_path" ]; then
        log "Verifying backup integrity: $backup_path"

        if [[ "$backup_path" == *.backup ]]; then
            # Verify custom format backup
            pg_restore --list "$backup_path" > /dev/null 2>&1
            if [ $? -eq 0 ]; then
                log "✅ Backup verification passed"
                return 0
            else
                log "❌ Backup verification failed"
                return 1
            fi
        fi
    fi

    return 0
}

# Main backup process
main() {
    log "🚀 Starting IABANK database backup process"
    log "Database: $DB_NAME on $DB_HOST:$DB_PORT"
    log "Backup directory: $BACKUP_DIR"

    # Check if PostgreSQL is available
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; then
        log "❌ PostgreSQL is not available"
        exit 1
    fi

    # Perform backups
    backup_success=false

    # Try basebackup first (preferred for PITR)
    if perform_basebackup; then
        backup_success=true
    else
        log "⚠️  Basebackup failed, trying logical dump..."
        if perform_logical_dump; then
            backup_success=true
        fi
    fi

    if [ "$backup_success" = false ]; then
        log "❌ All backup methods failed"
        exit 1
    fi

    # Cleanup old files
    cleanup_old_backups
    cleanup_old_wal

    # Show backup summary
    log "📊 Backup Summary:"
    log "- Total backups: $(find "$BACKUP_DIR" -name "basebackup_*" -o -name "dump_*.backup" | wc -l)"
    log "- Disk usage: $(du -sh "$BACKUP_DIR" | cut -f1)"

    log "✅ Backup process completed successfully"
}

# Run main function
main "$@"