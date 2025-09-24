"""Tasks Celery para rotinas financeiras."""
from __future__ import annotations

from decimal import Decimal
from typing import Dict

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q, Sum
from django.utils import timezone

from iabank.core.logging import get_logger
from iabank.core.models import Tenant
from iabank.finance.models import FinancialTransaction, TransactionStatus, TransactionType


logger = get_logger(__name__)

_DECIMAL_QUANTIZER = Decimal("0.01")


def _to_str_amount(value: Decimal) -> str:
    """Converte Decimal para string mantendo duas casas decimais."""

    return str(value.quantize(_DECIMAL_QUANTIZER))


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def generate_daily_reports(self) -> Dict[str, int]:
    """Gera snapshots diários de receitas e despesas por tenant."""

    reference_date = timezone.localdate()
    cache_ttl = getattr(settings, "FINANCE_DAILY_REPORT_TTL", 86400)
    processed = 0

    for tenant in Tenant.objects.filter(is_active=True).iterator():
        transactions = FinancialTransaction.objects.filter(
            tenant_id=tenant.id,
            status=TransactionStatus.PAID,
            reference_date=reference_date,
        )

        if not transactions.exists():
            cache_key = f"finance:reports:daily:{tenant.id}:{reference_date.isoformat()}"
            cache.delete(cache_key)
            continue

        totals = transactions.aggregate(
            income=Sum("amount", filter=Q(type=TransactionType.INCOME)),
            expenses=Sum("amount", filter=Q(type=TransactionType.EXPENSE)),
        )

        income_total = totals.get("income") or Decimal("0.00")
        expense_total = totals.get("expenses") or Decimal("0.00")
        net_total = income_total - expense_total

        snapshot = {
            "date": reference_date.isoformat(),
            "generated_at": timezone.now().isoformat(),
            "income": _to_str_amount(income_total),
            "expenses": _to_str_amount(expense_total),
            "net": _to_str_amount(net_total),
            "currency": tenant.settings.get("currency", "BRL"),
            "transactions": transactions.count(),
        }

        cache_key = f"finance:reports:daily:{tenant.id}:{reference_date.isoformat()}"
        cache.set(cache_key, snapshot, timeout=cache_ttl)
        processed += 1

    logger.info(
        "celery.generate_daily_reports.completed",
        reference_date=str(reference_date),
        processed_tenants=processed,
    )

    return {"tenants_processed": processed}


__all__ = ["generate_daily_reports"]
