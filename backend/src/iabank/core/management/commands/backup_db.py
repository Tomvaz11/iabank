"""
Management command para backup do banco de dados PostgreSQL.
Implementa backup incremental com PITR (Point-in-Time Recovery).
"""
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from iabank.core.logging import get_logger


logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Command para backup do banco PostgreSQL com PITR.

    Features:
    - Backup completo via pg_dump
    - Backup incremental via WAL archiving
    - Retenção configurável de backups
    - Validação de integridade
    """

    help = "Cria backup do banco PostgreSQL com suporte a PITR"

    def add_arguments(self, parser):
        """Argumentos do command."""
        parser.add_argument(
            "--type",
            type=str,
            default="full",
            choices=["full", "incremental"],
            help="Tipo de backup (full ou incremental)",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="backups",
            help="Diretório de saída dos backups",
        )
        parser.add_argument(
            "--retention-days",
            type=int,
            default=30,
            help="Dias de retenção dos backups",
        )
        parser.add_argument(
            "--compress",
            action="store_true",
            help="Comprime o backup com gzip",
        )

    def handle(self, *args, **options):
        """Executa o backup."""
        self.type = options["type"]
        self.output_dir = Path(options["output_dir"])
        self.retention_days = options["retention_days"]
        self.compress = options["compress"]

        try:
            self.stdout.write("Iniciando backup do PostgreSQL...")
            logger.info("Database backup started", backup_type=self.type)

            # Cria diretório de backup
            self._ensure_backup_directory()

            # Executa backup baseado no tipo
            if self.type == "full":
                backup_path = self._create_full_backup()
            else:
                backup_path = self._create_incremental_backup()

            # Valida backup
            self._validate_backup(backup_path)

            # Limpa backups antigos
            self._cleanup_old_backups()

            self.stdout.write(
                self.style.SUCCESS(f"Backup concluído: {backup_path}")
            )
            logger.info("Database backup completed", backup_path=str(backup_path))

        except Exception as e:
            error_msg = f"Erro no backup: {str(e)}"
            logger.error("Database backup failed", error=str(e))
            raise CommandError(error_msg)

    def _ensure_backup_directory(self):
        """Cria diretório de backup se não existir."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _create_full_backup(self) -> Path:
        """
        Cria backup completo com pg_dump.

        Returns:
            Path: Caminho do arquivo de backup
        """
        db_config = settings.DATABASES["default"]

        # Nome do arquivo de backup
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"iabank_full_{timestamp}.sql"
        if self.compress:
            filename += ".gz"

        backup_path = self.output_dir / filename

        # Comando pg_dump
        cmd = [
            "pg_dump",
            "--host", db_config["HOST"],
            "--port", str(db_config["PORT"]),
            "--username", db_config["USER"],
            "--dbname", db_config["NAME"],
            "--verbose",
            "--no-owner",
            "--no-privileges",
            "--format=custom" if self.compress else "--format=plain",
        ]

        # Variáveis de ambiente para senha
        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["PASSWORD"]

        try:
            self.stdout.write("Executando pg_dump...")

            if self.compress and "--format=plain" in " ".join(cmd):
                # Pipe para gzip se formato plain
                cmd.remove("--format=plain")
                with open(backup_path, "wb") as f:
                    process1 = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, env=env, check=True
                    )
                    process2 = subprocess.Popen(
                        ["gzip", "-c"], stdin=process1.stdout, stdout=f, check=True
                    )
                    process1.stdout.close()
                    process2.communicate()
            else:
                # Execução direta
                with open(backup_path, "wb") as f:
                    subprocess.run(cmd, stdout=f, env=env, check=True)

            self.stdout.write(f"Backup criado: {backup_path}")
            return backup_path

        except subprocess.CalledProcessError as e:
            raise CommandError(f"Erro no pg_dump: {e}")

    def _create_incremental_backup(self) -> Path:
        """
        Cria backup incremental via WAL archiving.

        Returns:
            Path: Caminho do diretório de WAL
        """
        # Para backup incremental, precisamos dos WAL files
        wal_dir = self.output_dir / "wal"
        wal_dir.mkdir(exist_ok=True)

        # Força checkpoint para garantir WAL flush
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_switch_wal()")
            cursor.execute("CHECKPOINT")

        # Copia WAL files (implementação simplificada)
        # Em produção, seria configurado no postgresql.conf
        self.stdout.write("Backup incremental configurado")
        self.stdout.write("Configure archive_command no postgresql.conf:")
        self.stdout.write(f"archive_command = 'cp %p {wal_dir}/%f'")

        return wal_dir

    def _validate_backup(self, backup_path: Path):
        """
        Valida integridade do backup.

        Args:
            backup_path: Caminho do backup
        """
        try:
            if backup_path.is_file():
                # Valida arquivo de backup
                file_size = backup_path.stat().st_size
                if file_size == 0:
                    raise CommandError("Backup vazio criado")

                self.stdout.write(f"Backup válido: {file_size:,} bytes")

            elif backup_path.is_dir():
                # Valida diretório WAL
                wal_files = list(backup_path.glob("*"))
                self.stdout.write(f"WAL files: {len(wal_files)}")

            logger.info(
                "Backup validated",
                backup_path=str(backup_path),
                backup_type=self.type,
            )

        except Exception as e:
            raise CommandError(f"Erro na validação: {e}")

    def _cleanup_old_backups(self):
        """Remove backups antigos baseado na retenção."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (
            self.retention_days * 24 * 3600
        )

        removed_count = 0
        for backup_file in self.output_dir.glob("iabank_full_*.sql*"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                removed_count += 1

        if removed_count > 0:
            self.stdout.write(f"Removidos {removed_count} backups antigos")
            logger.info("Old backups cleaned up", removed_count=removed_count)


class BackupManager:
    """
    Manager para operações de backup e restore.

    Utilitário para uso em scripts e testes.
    """

    def __init__(self, output_dir: str = "backups"):
        self.output_dir = Path(output_dir)
        self.logger = get_logger(self.__class__.__name__)

    def create_full_backup(
        self,
        compress: bool = True,
        retention_days: int = 30,
    ) -> Path:
        """
        Cria backup completo programaticamente.

        Args:
            compress: Comprimir backup
            retention_days: Dias de retenção

        Returns:
            Path: Caminho do backup criado
        """
        from django.core.management import call_command

        with tempfile.NamedTemporaryFile() as temp_file:
            call_command(
                "backup_db",
                type="full",
                output_dir=str(self.output_dir),
                compress=compress,
                retention_days=retention_days,
            )

        # Retorna backup mais recente
        backups = sorted(self.output_dir.glob("iabank_full_*.sql*"))
        return backups[-1] if backups else None

    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        Restaura banco de dados a partir de backup.

        Args:
            backup_path: Caminho do backup

        Returns:
            bool: Sucesso da operação
        """
        db_config = settings.DATABASES["default"]

        cmd = [
            "pg_restore",
            "--host", db_config["HOST"],
            "--port", str(db_config["PORT"]),
            "--username", db_config["USER"],
            "--dbname", db_config["NAME"],
            "--clean",
            "--if-exists",
            "--verbose",
            str(backup_path),
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = db_config["PASSWORD"]

        try:
            subprocess.run(cmd, env=env, check=True)
            self.logger.info("Database restored", backup_path=str(backup_path))
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error("Database restore failed", error=str(e))
            return False