"""Modelos do domínio de operações (empréstimos e parcelas)."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from iabank.core.models import BaseTenantModel, Tenant


REGRET_PERIOD_DAYS = 7
MIN_INSTALLMENTS = 1
MAX_INSTALLMENTS = 120


class LoanStatus(models.TextChoices):
    """Estados possíveis para um empréstimo."""

    ANALYSIS = "ANALYSIS", "Em análise"
    APPROVED = "APPROVED", "Aprovado"
    ACTIVE = "ACTIVE", "Ativo"
    FINISHED = "FINISHED", "Finalizado"
    COLLECTION = "COLLECTION", "Em cobrança"
    CANCELLED = "CANCELLED", "Cancelado"


class Loan(BaseTenantModel):
    """Representa um empréstimo concedido para um cliente."""

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="loans",
        help_text="Cliente associado ao empréstimo",
    )
    consultant = models.ForeignKey(
        "users.Consultant",
        on_delete=models.SET_NULL,
        related_name="loans",
        null=True,
        blank=True,
        help_text="Consultor responsável pelo empréstimo",
    )
    principal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor principal concedido ao cliente",
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Taxa de juros mensal aplicada ao empréstimo",
    )
    installments_count = models.PositiveIntegerField(
        validators=[
            MinValueValidator(MIN_INSTALLMENTS),
            MaxValueValidator(MAX_INSTALLMENTS),
        ],
        help_text="Quantidade total de parcelas do empréstimo",
    )
    iof_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Valor de IOF calculado para o empréstimo",
    )
    cet_monthly = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="CET mensal (Custo Efetivo Total)",
    )
    cet_yearly = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("0.0000"),
        help_text="CET anual (Custo Efetivo Total)",
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Valor total devido considerando juros e IOF",
    )
    contract_date = models.DateField(
        default=timezone.localdate,
        help_text="Data de assinatura do contrato",
    )
    first_due_date = models.DateField(
        help_text="Data de vencimento da primeira parcela",
    )
    status = models.CharField(
        max_length=15,
        choices=LoanStatus.choices,
        default=LoanStatus.ANALYSIS,
        help_text="Status atual do empréstimo",
    )
    regret_deadline = models.DateField(
        help_text="Prazo legal para arrependimento (7 dias)",
        blank=True,
        null=True,
    )
    notes = models.TextField(
        blank=True,
        help_text="Observações adicionais sobre o empréstimo",
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Controle de concorrência otimista",
    )

    class Meta:
        db_table = "operations_loans"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "status"],
                name="ops_loans_tenant_status_idx",
            ),
            models.Index(
                fields=["tenant_id", "customer"],
                name="ops_loans_tenant_customer_idx",
            ),
            models.Index(
                fields=["tenant_id", "contract_date"],
                name="ops_loans_tenant_contract_idx",
            ),
            models.Index(
                fields=["tenant_id", "consultant"],
                name="ops_loans_tenant_consultant_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(principal_amount__gt=0),
                name="ops_loans_principal_gt_zero",
            ),
            models.CheckConstraint(
                check=Q(interest_rate__gte=0),
                name="ops_loans_interest_rate_positive",
            ),
            models.CheckConstraint(
                check=Q(total_amount__gte=F("principal_amount")),
                name="ops_loans_total_gte_principal",
            ),
        ]

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        if not self.customer_id:
            errors["customer"] = "Empréstimo deve estar associado a um cliente válido."
        else:
            customer_tenant = getattr(self.customer, "tenant_id", None)
            if not customer_tenant:
                errors["customer"] = "Cliente associado não possui tenant válido."
            else:
                normalized_tenant = self._normalize_tenant_id(customer_tenant)
                if self.tenant_id and self.tenant_id != normalized_tenant:
                    errors["tenant_id"] = "tenant_id deve coincidir com o tenant do cliente."
                self.tenant_id = normalized_tenant

        if self.consultant_id:
            consultant_tenant = getattr(self.consultant, "tenant_id", None)
            if consultant_tenant != self.tenant_id:
                errors["consultant"] = "Consultor deve pertencer ao mesmo tenant do empréstimo."
            elif getattr(self.consultant, "is_active_for_loans", True) is False:
                errors["consultant"] = "Consultor não está ativo para originar empréstimos."

        if self.installments_count and not (MIN_INSTALLMENTS <= self.installments_count <= MAX_INSTALLMENTS):
            errors["installments_count"] = (
                f"Número de parcelas deve estar entre {MIN_INSTALLMENTS} e {MAX_INSTALLMENTS}."
            )

        if self.interest_rate is not None:
            max_rate = self._resolve_max_interest_rate()
            if max_rate is not None and self.interest_rate > max_rate:
                errors["interest_rate"] = (
                    "Taxa de juros informada excede o limite permitido para o tenant."
                )

        if self.contract_date and self.first_due_date:
            if self.first_due_date <= self.contract_date:
                errors["first_due_date"] = "Primeira parcela deve vencer após a data do contrato."

        if self.contract_date:
            expected_deadline = self.contract_date + timedelta(days=REGRET_PERIOD_DAYS)
            if self.regret_deadline and self.regret_deadline != expected_deadline:
                errors["regret_deadline"] = (
                    "Prazo de arrependimento deve ser exatamente 7 dias após a data do contrato."
                )
            self.regret_deadline = expected_deadline

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.contract_date:
            self.contract_date = timezone.localdate()

        self.full_clean()

        if self._state.adding:
            self.version = 1
        else:
            self.version = (self.version or 0) + 1

        super().save(*args, **kwargs)

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "customer_id": str(self.customer_id) if self.customer_id else None,
                "status": self.status,
                "principal_amount": str(self.principal_amount),
                "interest_rate": str(self.interest_rate),
                "installments_count": self.installments_count,
            }
        )
        return fields

    def _resolve_max_interest_rate(self) -> Optional[Decimal]:
        if not self.tenant_id:
            return None

        try:
            tenant_settings = (
                Tenant.objects.filter(id=self.tenant_id)
                .values_list("settings", flat=True)
                .first()
            )
        except Tenant.DoesNotExist:  # pragma: no cover - defensive
            return None

        if not tenant_settings:
            return None

        max_rate = tenant_settings.get("max_interest_rate")
        if max_rate is None:
            return None

        return Decimal(str(max_rate))

    def __str__(self) -> str:
        return f"Loan({self.id})"
