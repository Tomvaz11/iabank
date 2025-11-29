from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

REPO_ROOT = Path(__file__).resolve().parents[4]


class CheckMigrationsScriptTest(SimpleTestCase):
    def _run_script(self, base_path: Path) -> subprocess.CompletedProcess[str]:
        script = REPO_ROOT / "scripts/ci/check-migrations.sh"
        return subprocess.run(
            [str(script), "--path", str(base_path)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_allows_concurrent_index_when_atomic_flag_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "app" / "migrations"
            migrations_dir.mkdir(parents=True, exist_ok=True)
            migration_file = migrations_dir / "0001_atomic_concurrent.py"
            migration_file.write_text(
                "atomic = False\nfrom django.contrib.postgres.operations import AddIndexConcurrently\n",
            )

            result = self._run_script(Path(tmpdir))

            self.assertEqual(result.returncode, 0)
            self.assertIn("OK", result.stdout)

    def test_blocks_concurrent_index_without_atomic_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "app" / "migrations"
            migrations_dir.mkdir(parents=True, exist_ok=True)
            migration_file = migrations_dir / "0002_missing_atomic.py"
            migration_file.write_text(
                "from django.contrib.postgres.operations import AddIndexConcurrently\n",
            )

            result = self._run_script(Path(tmpdir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CONCURRENTLY", result.stderr + result.stdout)

    def test_blocks_destructive_drop_statements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            migrations_dir = Path(tmpdir) / "app" / "migrations"
            migrations_dir.mkdir(parents=True, exist_ok=True)
            migration_file = migrations_dir / "0003_drop_column.py"
            migration_file.write_text("DROP TABLE foo;")

            result = self._run_script(Path(tmpdir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("operacao destrutiva", result.stderr + result.stdout)
