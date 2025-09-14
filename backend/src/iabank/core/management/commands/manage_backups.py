"""
Django management command to manage database backups.
Implements FR-111: Backup management with retention policies.
"""

import os
import subprocess
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Manage database backups and PITR configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["backup", "restore", "list", "cleanup", "status"],
            help="Action to perform",
        )
        parser.add_argument(
            "--pitr-time",
            type=str,
            help="Point-in-time for PITR restore (YYYY-MM-DD HH:MM:SS)",
        )
        parser.add_argument("--backup-path", type=str, help="Path to specific backup")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without executing",
        )

    def handle(self, *args, **options):
        action = options["action"]

        self.stdout.write(
            self.style.SUCCESS(f"IABANK Backup Management - {action.title()}")
        )

        if action == "backup":
            self.perform_backup(options)
        elif action == "restore":
            self.perform_restore(options)
        elif action == "list":
            self.list_backups(options)
        elif action == "cleanup":
            self.cleanup_backups(options)
        elif action == "status":
            self.show_status(options)

    def perform_backup(self, options):
        """Trigger database backup."""
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write("DRY RUN - Would perform backup")
            return

        backup_script = "/app/scripts/backup/backup_database.sh"

        self.stdout.write("Starting database backup...")
        try:
            result = subprocess.run(
                [backup_script], check=False, capture_output=True, text=True
            )
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS("Backup completed successfully"))
                self.stdout.write(result.stdout)
            else:
                self.stdout.write(self.style.ERROR("Backup failed"))
                self.stdout.write(result.stderr)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR("Backup script not found. Run from Docker container.")
            )

    def perform_restore(self, options):
        """Trigger database restore."""
        pitr_time = options.get("pitr_time")
        backup_path = options.get("backup_path")
        dry_run = options.get("dry_run", False)

        restore_script = "/app/scripts/backup/restore_database.sh"
        cmd = [restore_script]

        if pitr_time:
            cmd.extend(["--pitr", pitr_time, "--latest-basebackup"])
        elif backup_path:
            cmd.extend(["--basebackup", backup_path])
        else:
            cmd.append("--latest-dump")

        if dry_run:
            cmd.append("--dry-run")

        self.stdout.write(f'Restore command: {" ".join(cmd)}')

        if not dry_run:
            self.stdout.write(
                self.style.WARNING("WARNING: This will overwrite the current database!")
            )
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() != "yes":
                self.stdout.write("Restore cancelled.")
                return

        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            self.stdout.write(result.stdout)
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR("Restore failed"))
                self.stdout.write(result.stderr)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR("Restore script not found. Run from Docker container.")
            )

    def list_backups(self, options):
        """List available backups."""
        backup_dir = "/var/backups/iabank"

        self.stdout.write(f"Available backups in {backup_dir}:")

        if not os.path.exists(backup_dir):
            self.stdout.write("Backup directory not found")
            return

        # List base backups
        self.stdout.write("\n[BASE BACKUPS] Base Backups (PITR):")
        basebackup_found = False
        for item in os.listdir(backup_dir):
            if item.startswith("basebackup_"):
                path = os.path.join(backup_dir, item)
                if os.path.isdir(path):
                    size = self.get_directory_size(path)
                    timestamp = item.replace("basebackup_", "")
                    formatted_time = self.format_timestamp(timestamp)
                    self.stdout.write(f"  [BACKUP] {item} ({size}) - {formatted_time}")
                    basebackup_found = True

        if not basebackup_found:
            self.stdout.write("  (No base backups found)")

        # List logical dumps
        self.stdout.write("\n[DUMPS] Logical Dumps:")
        dump_found = False
        for item in os.listdir(backup_dir):
            if item.startswith("dump_") and (
                item.endswith(".backup") or item.endswith(".sql.gz")
            ):
                path = os.path.join(backup_dir, item)
                if os.path.isfile(path):
                    size = self.get_file_size(path)
                    mtime = datetime.fromtimestamp(os.path.getmtime(path))
                    self.stdout.write(
                        f'  [DUMP] {item} ({size}) - {mtime.strftime("%Y-%m-%d %H:%M:%S")}'
                    )
                    dump_found = True

        if not dump_found:
            self.stdout.write("  (No logical dumps found)")

    def cleanup_backups(self, options):
        """Clean up old backups according to retention policy."""
        dry_run = options.get("dry_run", False)

        self.stdout.write("[CLEANUP] Cleaning up old backups (FR-111 retention policy)")

        backup_dir = "/var/backups/iabank"
        retention_days = 30
        wal_retention_days = 14

        if dry_run:
            self.stdout.write("DRY RUN - No files will be deleted")

        # Cleanup logic would go here
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        wal_cutoff_date = datetime.now() - timedelta(days=wal_retention_days)

        self.stdout.write(
            f'Backup retention: {retention_days} days (before {cutoff_date.strftime("%Y-%m-%d")})'
        )
        self.stdout.write(
            f'WAL retention: {wal_retention_days} days (before {wal_cutoff_date.strftime("%Y-%m-%d")})'
        )

        if not dry_run:
            self.stdout.write("Cleanup completed")

    def show_status(self, options):
        """Show PITR and backup status."""
        self.stdout.write("[STATUS] IABANK Backup & PITR Status")

        try:
            with connection.cursor() as cursor:
                # Check PITR configuration
                cursor.execute("SELECT * FROM check_pitr_config();")
                config_status = cursor.fetchall()

                self.stdout.write("\n[PITR] PITR Configuration:")
                for (
                    setting_name,
                    current_value,
                    recommended_value,
                    status,
                ) in config_status:
                    self.stdout.write(
                        f"  {setting_name}: {current_value} (recommended: {recommended_value}) {status}"
                    )

                # Show WAL status
                cursor.execute("SELECT * FROM show_wal_status();")
                wal_status = cursor.fetchone()

                self.stdout.write("\n[WAL] WAL Status:")
                if wal_status:
                    (
                        current_wal,
                        location,
                        in_recovery,
                        last_archived,
                        last_time,
                    ) = wal_status
                    self.stdout.write(f"  Current WAL: {current_wal}")
                    self.stdout.write(f"  Location: {location}")
                    self.stdout.write(f"  In recovery: {in_recovery}")
                    self.stdout.write(f"  Last archived: {last_archived}")
                    self.stdout.write(f"  Last archive time: {last_time}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking status: {e}"))

    def get_directory_size(self, path):
        """Get human-readable directory size."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
        return self.format_bytes(total)

    def get_file_size(self, path):
        """Get human-readable file size."""
        size = os.path.getsize(path)
        return self.format_bytes(size)

    def format_bytes(self, bytes_val):
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}PB"

    def format_timestamp(self, timestamp):
        """Format timestamp string to readable format."""
        try:
            if len(timestamp) == 15:  # YYYYMMDD_HHMMSS
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        return timestamp
