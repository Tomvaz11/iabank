"""Tasks Celery para rotinas do módulo de operações."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Set

from celery import shared_task
from decouple import UndefinedValueError, config as env_config
from django.conf import settings
from django.utils import timezone

from iabank.core.logging import get_logger
from iabank.core.models import Tenant
from iabank.operations.domain.entities import (
    InstallmentEntity,
    InstallmentStatus as DomainInstallmentStatus,
    LoanEntity,
    LoanStatus,
)
from iabank.operations.domain.services import (
    DEFAULT_IOF_DAILY_RATE,
    DEFAULT_IOF_FIXED_RATE,
    InstallmentService,
    LoanService,
    LoanStatusTransitionError,
)
from iabank.operations.models import Installment, InstallmentStatus, Loan


logger = get_logger(__name__)


def _decimal_from_config(var_name: str, default: Decimal) -> Decimal:
    """Resolve valores decimais a partir do environment com fallback seguro."""

    try:
        raw_value = env_config(var_name, default=str(default))
    except UndefinedValueError:  # pragma: no cover - proteção extra
        raw_value = str(default)

    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        logger.warning(
            "celery.invalid_regulatory_rate",
            variable=var_name,
            value=raw_value,
            default=str(default),
        )
        return Decimal(default)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
def update_iof_rates(self) -> Dict[str, str]:
    """Sincroniza taxas de IOF com base em configuração centralizada."""

    fixed_rate = _decimal_from_config("IOF_FIXED_RATE", DEFAULT_IOF_FIXED_RATE)
    daily_rate = _decimal_from_config("IOF_DAILY_RATE", DEFAULT_IOF_DAILY_RATE)

    updated_tenants = 0
    now = timezone.now()

    for tenant in Tenant.objects.filter(is_active=True).iterator():
        current_settings = dict(tenant.settings or {})
        needs_update = (
            str(current_settings.get("iof_fixed_rate")) != str(fixed_rate)
            or str(current_settings.get("iof_daily_rate")) != str(daily_rate)
        )

        if not needs_update and current_settings.get("iof_last_synced_at"):
            continue

        current_settings.update(
            {
                "iof_fixed_rate": str(fixed_rate),
                "iof_daily_rate": str(daily_rate),
                "iof_last_synced_at": now.isoformat(),
            }
        )

        Tenant.objects.filter(pk=tenant.pk).update(
            settings=current_settings,
            updated_at=now,
        )
        updated_tenants += 1

    logger.info(
        "celery.iof_rates_synchronized",
        updated_tenants=updated_tenants,
        fixed_rate=str(fixed_rate),
        daily_rate=str(daily_rate),
    )

    return {
        "updated_tenants": str(updated_tenants),
        "fixed_rate": str(fixed_rate),
        "daily_rate": str(daily_rate),
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True)
def calculate_overdue_interest(self) -> Dict[str, int]:
    """Aplica encargos de atraso e move empréstimos para cobrança quando necessário."""

    reference_date = timezone.localdate()
    grace_days = getattr(settings, "OPERATIONS_INSTALLMENT_GRACE_DAYS", 5)

    cutoff_date = reference_date - timedelta(days=grace_days)
    installments_qs = (
        Installment.objects.filter(
            due_date__lt=cutoff_date,
        )
        .exclude(status=InstallmentStatus.PAID)
        .select_related("loan")
        .iterator()
    )

    updated_installments = 0
    loans_to_collection: Set[str] = set()

    for installment in installments_qs:
        entity = InstallmentEntity.model_validate(installment)
        updated_entity = InstallmentService.apply_overdue_interest(
            entity,
            reference_date=reference_date,
            grace_days=grace_days,
        )

        has_changes = (
            updated_entity.late_fee != installment.late_fee
            or updated_entity.interest_penalty != installment.interest_penalty
            or updated_entity.status.value != installment.status
        )

        if has_changes:
            Installment.objects.filter(pk=installment.pk).update(
                late_fee=updated_entity.late_fee,
                interest_penalty=updated_entity.interest_penalty,
                status=updated_entity.status.value,
                updated_at=timezone.now(),
            )
            updated_installments += 1

        if (
            updated_entity.status is DomainInstallmentStatus.OVERDUE
            and installment.loan.status == LoanStatus.ACTIVE.value
        ):
            loans_to_collection.add(str(installment.loan_id))

    updated_loans = 0
    for loan_id in loans_to_collection:
        try:
            loan = Loan.objects.get(pk=loan_id)
        except Loan.DoesNotExist:  # pragma: no cover - consistência defensiva
            continue

        if loan.status == LoanStatus.COLLECTION.value:
            continue

        loan_entity = LoanEntity.model_validate(loan)
        try:
            updated_loan = LoanService.change_status(
                loan_entity,
                new_status=LoanStatus.COLLECTION,
                reference_date=reference_date,
            )
        except LoanStatusTransitionError:
            continue

        Loan.objects.filter(pk=loan.pk).update(
            status=updated_loan.status.value,
            updated_at=timezone.now(),
        )
        updated_loans += 1

    logger.info(
        "celery.calculate_overdue_interest.completed",
        updated_installments=updated_installments,
        updated_loans=updated_loans,
        reference_date=str(reference_date),
        grace_days=grace_days,
    )

    return {
        "updated_installments": updated_installments,
        "updated_loans": updated_loans,
    }


__all__ = [
    "calculate_overdue_interest",
    "update_iof_rates",
]
