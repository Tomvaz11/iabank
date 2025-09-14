#!/bin/bash
# IABANK Database Restore Script
# Implements FR-109: Point-in-Time Recovery (PITR)
# Supports both basebackup and logical dump restoration

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/iabank"
DB_NAME="iabank"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
PGDATA="/var/lib/postgresql/data/pgdata"
WAL_ARCHIVE_DIR="/var/lib/postgresql/wal_archive"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Show usage
usage() {
    cat << EOF
IABANK Database Restore Script

Usage: $0 [OPTIONS]

PITR Restore Options:
  --pitr TIMESTAMP          Restore to specific point in time (YYYY-MM-DD HH:MM:SS)
  --basebackup PATH         Path to base backup directory
  --latest-basebackup       Use the latest available base backup

Logical Restore Options:
  --dump PATH               Restore from logical dump file
  --latest-dump             Use the latest available dump

General Options:
  --target-db NAME          Target database name (default: $DB_NAME)
  --dry-run                 Show what would be done without executing
  --help                    Show this help message

Examples:
  # PITR to specific timestamp
  $0 --pitr "2024-01-15 14:30:00" --latest-basebackup

  # Restore from specific base backup
  $0 --basebackup /var/backups/iabank/basebackup_20240115_143000

  # Restore from latest dump
  $0 --latest-dump

  # Dry run to see available backups
  $0 --dry-run
EOF
}

# List available backups
list_backups() {
    log "📋 Available backups in $BACKUP_DIR:"

    echo
    echo "Base Backups (PITR):"
    if ls "$BACKUP_DIR"/basebackup_* 1> /dev/null 2>&1; then
        for backup in "$BACKUP_DIR"/basebackup_*; do
            if [ -d "$backup" ]; then
                local timestamp=$(basename "$backup" | sed 's/basebackup_//')
                local size=$(du -sh "$backup" | cut -f1)
                echo "  📦 $backup ($size) - $(date -d "${timestamp:0:8} ${timestamp:9:2}:${timestamp:11:2}:${timestamp:13:2}" '+%Y-%m-%d %H:%M:%S')"
            fi
        done
    else
        echo "  (No base backups found)"
    fi

    echo
    echo "Logical Dumps:"
    if ls "$BACKUP_DIR"/dump_*.backup 1> /dev/null 2>&1; then
        for dump in "$BACKUP_DIR"/dump_*.backup; do
            if [ -f "$dump" ]; then
                local size=$(du -sh "$dump" | cut -f1)
                local date=$(stat -c %y "$dump" | cut -d' ' -f1-2)
                echo "  📄 $dump ($size) - $date"
            fi
        done
    else
        echo "  (No logical dumps found)"
    fi
    echo
}

# Get latest base backup
get_latest_basebackup() {
    ls -dt "$BACKUP_DIR"/basebackup_* 2>/dev/null | head -n1 || echo ""
}

# Get latest dump
get_latest_dump() {
    ls -dt "$BACKUP_DIR"/dump_*.backup 2>/dev/null | head -n1 || echo ""
}

# Perform PITR restore
perform_pitr_restore() {
    local basebackup_path="$1"
    local target_time="$2"

    log "🔄 Starting Point-in-Time Recovery"
    log "Base backup: $basebackup_path"
    log "Target time: $target_time"

    # Verify base backup exists
    if [ ! -d "$basebackup_path" ]; then
        log "❌ Base backup not found: $basebackup_path"
        return 1
    fi

    # Stop PostgreSQL if running
    log "Stopping PostgreSQL..."
    if pgrep postgres > /dev/null; then
        pkill postgres || true
        sleep 5
    fi

    # Backup current data directory
    if [ -d "$PGDATA" ]; then
        local backup_current="$PGDATA.backup.$(date +%Y%m%d_%H%M%S)"
        log "Backing up current data directory to: $backup_current"
        mv "$PGDATA" "$backup_current"
    fi

    # Restore base backup
    log "Restoring base backup..."
    mkdir -p "$PGDATA"

    # Extract base backup
    for tarfile in "$basebackup_path"/base.tar.gz; do
        if [ -f "$tarfile" ]; then
            tar -xzf "$tarfile" -C "$PGDATA"
            break
        fi
    done

    # Extract WAL files if present
    for tarfile in "$basebackup_path"/pg_wal.tar.gz; do
        if [ -f "$tarfile" ]; then
            tar -xzf "$tarfile" -C "$PGDATA/pg_wal"
            break
        fi
    done

    # Create recovery configuration
    cat > "$PGDATA/postgresql.auto.conf" << EOF
# PITR Recovery Configuration
restore_command = 'cp $WAL_ARCHIVE_DIR/%f %p'
recovery_target_time = '$target_time'
recovery_target_action = 'promote'
EOF

    # Create recovery signal file (PostgreSQL 12+)
    touch "$PGDATA/recovery.signal"

    # Set proper permissions
    chmod 700 "$PGDATA"
    chown -R postgres:postgres "$PGDATA" 2>/dev/null || true

    log "✅ PITR configuration completed"
    log "Start PostgreSQL to begin recovery process"
    log "Recovery will stop at: $target_time"
}

# Perform logical restore
perform_logical_restore() {
    local dump_path="$1"
    local target_db="$2"

    log "🔄 Starting logical restore"
    log "Dump file: $dump_path"
    log "Target database: $target_db"

    # Verify dump exists
    if [ ! -f "$dump_path" ]; then
        log "❌ Dump file not found: $dump_path"
        return 1
    fi

    # Check if PostgreSQL is available
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; then
        log "❌ PostgreSQL is not available"
        return 1
    fi

    # Drop and recreate database
    log "Recreating database: $target_db"
    dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$target_db"
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$target_db"

    # Restore from dump
    if [[ "$dump_path" == *.backup ]]; then
        log "Restoring from custom format dump..."
        pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$target_db" \
            --verbose \
            --clean \
            --if-exists \
            --no-owner \
            --no-privileges \
            "$dump_path"
    elif [[ "$dump_path" == *.sql.gz ]]; then
        log "Restoring from compressed SQL dump..."
        gunzip -c "$dump_path" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$target_db"
    else
        log "❌ Unsupported dump format: $dump_path"
        return 1
    fi

    log "✅ Logical restore completed"
}

# Main function
main() {
    local pitr_time=""
    local basebackup_path=""
    local dump_path=""
    local target_db="$DB_NAME"
    local dry_run=false
    local latest_basebackup=false
    local latest_dump=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --pitr)
                pitr_time="$2"
                shift 2
                ;;
            --basebackup)
                basebackup_path="$2"
                shift 2
                ;;
            --latest-basebackup)
                latest_basebackup=true
                shift
                ;;
            --dump)
                dump_path="$2"
                shift 2
                ;;
            --latest-dump)
                latest_dump=true
                shift
                ;;
            --target-db)
                target_db="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log "❌ Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    log "🚀 IABANK Database Restore Script"

    # Show available backups if dry run
    if [ "$dry_run" = true ]; then
        list_backups
        exit 0
    fi

    # Get latest backups if requested
    if [ "$latest_basebackup" = true ]; then
        basebackup_path=$(get_latest_basebackup)
        if [ -z "$basebackup_path" ]; then
            log "❌ No base backups found"
            exit 1
        fi
        log "Using latest base backup: $basebackup_path"
    fi

    if [ "$latest_dump" = true ]; then
        dump_path=$(get_latest_dump)
        if [ -z "$dump_path" ]; then
            log "❌ No dumps found"
            exit 1
        fi
        log "Using latest dump: $dump_path"
    fi

    # Perform restore based on options
    if [ -n "$pitr_time" ] && [ -n "$basebackup_path" ]; then
        perform_pitr_restore "$basebackup_path" "$pitr_time"
    elif [ -n "$dump_path" ]; then
        perform_logical_restore "$dump_path" "$target_db"
    else
        log "❌ No valid restore options specified"
        usage
        exit 1
    fi
}

# Run main function
main "$@"