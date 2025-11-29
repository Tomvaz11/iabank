from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import BudgetRateLimit, SeedProfile


DEFAULT_COST_MODEL_PATH = Path(__file__).resolve().parents[4] / 'configs' / 'finops' / 'seed-data.cost-model.yaml'


@dataclass
class BudgetSnapshot:
    limit: int
    window_seconds: int
    cost_cap: float
    error_budget_pct: float
    cost_model_version: str
    budget_alert_pct: float


class BudgetService:
    """
    Provisiona e avalia limites de rate-limit/FinOps para execuções de seeds.
    """

    def __init__(self, cost_model_path: Path | None = None) -> None:
        self.cost_model_path = cost_model_path or DEFAULT_COST_MODEL_PATH
        self.cost_model = self._load_cost_model()

    def _load_cost_model(self) -> Dict[str, Any]:
        if not self.cost_model_path.exists():
            raise RuntimeError(f'Cost model não encontrado em {self.cost_model_path}')

        content = self.cost_model_path.read_text(encoding='utf-8')
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore
            except Exception:
                yaml = None
            data = yaml.safe_load(content) if 'yaml' in locals() and yaml else {}

        if not isinstance(data, dict):
            raise RuntimeError('Cost model inválido: esperado objeto JSON/YAML.')
        required_keys = ('schema_version', 'model_version')
        for key in required_keys:
            if key not in data or not str(data.get(key)).strip():
                raise RuntimeError(f'Cost model inválido: chave obrigatória ausente ({key}).')
        return data

    def environment_allowed(self, *, mode: str, environment: str) -> bool:
        required = set(self.cost_model.get('worm', {}).get('required_environments', []))
        if mode in {'carga', 'dr'} and required and environment not in required:
            return False
        return True

    def required_environments(self) -> set[str]:
        return set(self.cost_model.get('worm', {}).get('required_environments', []))

    def worm_required(self, mode: str) -> bool:
        mode_cfg = (self.cost_model.get('modes') or {}).get(mode, {})
        return bool(mode_cfg.get('worm_required'))

    def snapshot_from_profile(self, seed_profile: SeedProfile) -> BudgetSnapshot:
        env_cfg = (self.cost_model.get('environments') or {}).get(seed_profile.environment, {})
        mode_cfg = (self.cost_model.get('modes') or {}).get(seed_profile.mode, {})
        rate_limit = seed_profile.rate_limit or {}
        limit = rate_limit.get('limit', env_cfg.get('rate_limit_rpm', 1))
        window_seconds = rate_limit.get('window_seconds', 60)
        budget_cfg = seed_profile.budget or {}
        cost_cap = budget_cfg.get('cost_cap_brl', env_cfg.get('cost_cap_brl', 0))
        error_budget = budget_cfg.get('error_budget_pct', env_cfg.get('error_budget_pct', 0))
        budget_alert_pct = mode_cfg.get('budget_alert_pct', 80)

        return BudgetSnapshot(
            limit=max(1, int(limit or 1)),
            window_seconds=max(1, int(window_seconds or 60)),
            cost_cap=float(cost_cap or 0),
            error_budget_pct=float(error_budget or 0),
            cost_model_version=str(self.cost_model.get('model_version', '')),
            budget_alert_pct=float(budget_alert_pct or 80),
        )

    def ensure_budget_for_profile(
        self,
        seed_profile: SeedProfile,
        *,
        snapshot: BudgetSnapshot | None = None,
    ) -> BudgetRateLimit:
        snap = snapshot or self.snapshot_from_profile(seed_profile)
        now = timezone.now()
        reset_at = now + timedelta(seconds=snap.window_seconds)
        cost_window_end = now + timedelta(days=1)

        with use_tenant(seed_profile.tenant_id):
            budget, _ = BudgetRateLimit.objects.update_or_create(
                seed_profile=seed_profile,
                defaults={
                    'tenant_id': seed_profile.tenant_id,
                    'environment': seed_profile.environment,
                    'rate_limit_limit': snap.limit,
                    'rate_limit_window_seconds': snap.window_seconds,
                    'rate_limit_remaining': snap.limit,
                    'reset_at': reset_at,
                    'budget_cost_cap': snap.cost_cap,
                    'budget_cost_estimated': snap.cost_cap,
                    'budget_cost_actual': 0,
                    'error_budget': snap.error_budget_pct,
                    'throughput_target_rps': seed_profile.slo_throughput_rps,
                    'budget_alert_at_pct': snap.budget_alert_pct,
                    'cost_model_version': snap.cost_model_version,
                    'cost_window_started_at': now,
                    'cost_window_ends_at': cost_window_end,
                    'consumed_at': now,
                },
            )
        return budget

    def rate_limit_usage(self, snapshot: BudgetSnapshot, *, now: Optional[datetime] = None) -> dict[str, object]:
        current = now or timezone.now()
        reset_at = current + timedelta(seconds=snapshot.window_seconds)
        return {'limit': snapshot.limit, 'remaining': snapshot.limit, 'reset_at': reset_at.isoformat()}
