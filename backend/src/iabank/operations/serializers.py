"""Serializers para empréstimos, parcelas e pagamentos."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from iabank.core.exceptions import BusinessRuleViolation
from iabank.core.models import Tenant
from iabank.customers.models import Customer
from iabank.operations.domain.entities import (
    InstallmentEntity,
    LoanEntity,
    LoanStatus,
)
from iabank.operations.domain.services import (
    InstallmentPaymentError,
    InstallmentPaymentInput,
    InstallmentPlan,
    InstallmentService,
    InterestRateLimitError,
    LoanCalculationResult,
    LoanCancellationError,
    LoanCancellationInput,
    LoanCreateInput,
    LoanDomainError,
    LoanService,
    LoanStatusTransitionError,
    LoanStatusUpdateInput,
)
from iabank.operations.models import Installment, InstallmentStatus, Loan
from iabank.users.models import Consultant, User


def _resolve_tenant_id(request) -> UUID:
    tenant_candidate = getattr(request, "tenant_id", None)
    if tenant_candidate is None and getattr(request, "user", None) is not None:
        tenant_candidate = getattr(request.user, "tenant_id", None)
    if tenant_candidate is None:
        raise DRFValidationError({"tenant": ["Tenant não identificado na requisição."]})
    try:
        return UUID(str(tenant_candidate))
    except (TypeError, ValueError) as exc:
        raise DRFValidationError({"tenant": ["Tenant inválido"]}) from exc


def _get_tenant_settings(tenant_id: UUID) -> Dict[str, Any]:
    settings_dict = (
        Tenant.objects.filter(id=tenant_id)
        .values_list("settings", flat=True)
        .first()
    )
    if not settings_dict:
        return {}
    return dict(settings_dict)


def _map_domain_validation_error(exc: PydanticValidationError) -> Dict[str, Any]:
    errors: Dict[str, Any] = {}
    for err in exc.errors():
        field = err.get("loc", ("detail",))[-1]
        errors.setdefault(str(field), []).append(str(err.get("msg")))
    return errors


class LoanInstallmentOutputSerializer(serializers.ModelSerializer):
    """Serializa parcelas de empréstimo."""

    class Meta:
        model = Installment
        fields = (
            "id",
            "sequence",
            "due_date",
            "principal_amount",
            "interest_amount",
            "total_amount",
            "amount_paid",
            "late_fee",
            "interest_penalty",
            "status",
            "payment_date",
        )
        read_only_fields = fields


class LoanOutputSerializer(serializers.ModelSerializer):
    """Serializa empréstimos com dados agregados."""

    customer = serializers.SerializerMethodField()
    consultant = serializers.SerializerMethodField()
    installments = LoanInstallmentOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = (
            "id",
            "customer",
            "consultant",
            "principal_amount",
            "interest_rate",
            "installments_count",
            "iof_amount",
            "cet_monthly",
            "cet_yearly",
            "total_amount",
            "contract_date",
            "first_due_date",
            "status",
            "regret_deadline",
            "notes",
            "installments",
        )
        read_only_fields = fields

    def get_customer(self, obj: Loan) -> Optional[Dict[str, Any]]:
        if not obj.customer_id:
            return None
        customer = obj.customer
        return {
            "id": str(customer.id),
            "name": customer.name,
            "document": customer.document,
        }

    def get_consultant(self, obj: Loan) -> Optional[Dict[str, Any]]:
        consultant = getattr(obj, "consultant", None)
        if not consultant:
            return None
        user = consultant.user
        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }


class LoanCreateSerializer(serializers.Serializer):
    """Serializer para criação de empréstimos utilizando camada de domínio."""

    customer_id = serializers.UUIDField()
    principal_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=7, decimal_places=4)
    installments_count = serializers.IntegerField(min_value=1, max_value=120)
    first_due_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Request não disponível no contexto do serializer."]})

        tenant_id = _resolve_tenant_id(request)

        try:
            customer = Customer.objects.get(id=attrs["customer_id"], tenant_id=tenant_id)
        except Customer.DoesNotExist as exc:
            raise DRFValidationError({"customer_id": ["Cliente não encontrado para este tenant."]}) from exc

        consultant: Optional[Consultant] = None
        user: Optional[User] = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            consultant = getattr(user, "consultant_profile", None)

        tenant_settings = _get_tenant_settings(tenant_id)
        max_interest_rate_raw = tenant_settings.get("max_interest_rate")
        max_interest_rate = Decimal(str(max_interest_rate_raw)) if max_interest_rate_raw is not None else None

        create_input = LoanCreateInput(
            tenant_id=tenant_id,
            customer_id=customer.id,
            consultant_id=consultant.id if consultant else None,
            principal_amount=attrs["principal_amount"],
            interest_rate=attrs["interest_rate"],
            installments_count=attrs["installments_count"],
            first_due_date=attrs["first_due_date"],
            notes=attrs.get("notes"),
            max_interest_rate=max_interest_rate,
            contract_date=date.today(),
        )

        try:
            domain_result = LoanService.create_loan(create_input)
        except InterestRateLimitError as exc:
            raise DRFValidationError({"interest_rate": [str(exc)]}) from exc
        except (LoanDomainError, ValueError) as exc:
            raise DRFValidationError({"detail": [str(exc)]}) from exc
        except PydanticValidationError as exc:
            raise DRFValidationError(_map_domain_validation_error(exc)) from exc

        attrs["_tenant_id"] = tenant_id
        attrs["_customer"] = customer
        attrs["_consultant"] = consultant
        attrs["_domain_result"] = domain_result
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Loan:
        domain_result: LoanCalculationResult = validated_data["_domain_result"]
        customer: Customer = validated_data["_customer"]
        consultant: Optional[Consultant] = validated_data.get("_consultant")
        tenant_id: UUID = validated_data["_tenant_id"]

        loan_entity: LoanEntity = domain_result.loan
        notes = loan_entity.notes or ""

        with transaction.atomic():
            loan = Loan.objects.create(
                tenant_id=tenant_id,
                customer=customer,
                consultant=consultant,
                principal_amount=loan_entity.principal_amount,
                interest_rate=loan_entity.interest_rate,
                installments_count=loan_entity.installments_count,
                iof_amount=loan_entity.iof_amount,
                cet_monthly=loan_entity.cet_monthly,
                cet_yearly=loan_entity.cet_yearly,
                total_amount=loan_entity.total_amount,
                contract_date=loan_entity.contract_date,
                first_due_date=loan_entity.first_due_date,
                status=loan_entity.status.value,
                regret_deadline=loan_entity.regret_deadline,
                notes=notes,
            )

            installments_to_create: list[Installment] = []
            for plan in domain_result.installments:
                if not isinstance(plan, InstallmentPlan):
                    continue
                installments_to_create.append(
                    Installment(
                        tenant_id=tenant_id,
                        loan=loan,
                        sequence=plan.sequence,
                        due_date=plan.due_date,
                        principal_amount=plan.principal_amount,
                        interest_amount=plan.interest_amount,
                        total_amount=plan.total_amount,
                        amount_paid=Decimal("0.00"),
                        late_fee=Decimal("0.00"),
                        interest_penalty=Decimal("0.00"),
                        status=InstallmentStatus.PENDING,
                    )
                )

            if installments_to_create:
                Installment.objects.bulk_create(installments_to_create)

            loan.refresh_from_db()
            return loan


class LoanUpdateSerializer(serializers.Serializer):
    """Permite atualização segura de informações do empréstimo."""

    status = serializers.ChoiceField(
        choices=[(status.value, status.value) for status in LoanStatus],
        required=True,
    )

    def update(self, instance: Loan, validated_data: Dict[str, Any]) -> Loan:
        new_status = LoanStatus(validated_data["status"])
        entity = LoanEntity.model_validate(instance)
        try:
            updated_entity = LoanService.change_status(entity, new_status=new_status)
        except LoanStatusTransitionError as exc:
            raise DRFValidationError({"status": [str(exc)]}) from exc
        instance.status = updated_entity.status.value
        instance.save(update_fields=["status", "updated_at"])
        return instance

    def create(self, validated_data: Dict[str, Any]) -> Loan:  # pragma: no cover - DRF requirement
        raise NotImplementedError


class LoanCancellationSerializer(serializers.Serializer):
    """Valida cancelamento de empréstimo."""

    reason = serializers.CharField(min_length=3, max_length=500)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        attrs.setdefault("reference_date", timezone.localdate())
        try:
            cancellation_input = LoanCancellationInput(**attrs)
        except PydanticValidationError as exc:
            raise DRFValidationError(_map_domain_validation_error(exc)) from exc
        attrs["_domain_input"] = cancellation_input
        return attrs

    def save(self, **kwargs) -> Loan:
        loan: Loan = self.context["loan"]
        entity = LoanEntity.model_validate(loan)
        cancellation_input: LoanCancellationInput = self.validated_data["_domain_input"]
        try:
            updated = LoanService.cancel(entity, cancellation_input)
        except LoanCancellationError as exc:
            raise BusinessRuleViolation(str(exc), rule_code="LOAN_CANCELLATION_OUT_OF_WINDOW") from exc

        loan.status = updated.status.value
        loan.save(update_fields=["status", "updated_at"])
        return loan


class InstallmentPaymentSerializer(serializers.Serializer):
    """Processa pagamento de parcela utilizando domínio."""

    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_date = serializers.DateField()
    payment_method = serializers.CharField(required=False, allow_blank=True)
    bank_account_id = serializers.UUIDField(required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            payment_input = InstallmentPaymentInput(**attrs)
        except PydanticValidationError as exc:
            raise DRFValidationError(_map_domain_validation_error(exc)) from exc
        attrs["_domain_input"] = payment_input
        return attrs

    def save(self, **kwargs) -> Installment:
        installment: Installment = self.context["installment"]
        entity = InstallmentEntity.model_validate(installment)
        payment_input: InstallmentPaymentInput = self.validated_data["_domain_input"]

        try:
            updated_entity = InstallmentService.apply_payment(entity, payment_input)
        except InstallmentPaymentError as exc:
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        update_fields = {
            "amount_paid": updated_entity.amount_paid,
            "late_fee": updated_entity.late_fee,
            "interest_penalty": updated_entity.interest_penalty,
            "status": updated_entity.status.value,
            "payment_date": updated_entity.payment_date,
        }
        for field, value in update_fields.items():
            setattr(installment, field, value)

        try:
            installment.save(update_fields=[
                "amount_paid",
                "late_fee",
                "interest_penalty",
                "status",
                "payment_date",
                "updated_at",
            ])
        except IntegrityError as exc:
            raise DRFValidationError({"detail": ["Falha ao registrar pagamento."]}) from exc

        return installment


__all__ = [
    "InstallmentPaymentSerializer",
    "LoanCancellationSerializer",
    "LoanCreateSerializer",
    "LoanInstallmentOutputSerializer",
    "LoanOutputSerializer",
    "LoanUpdateSerializer",
]
