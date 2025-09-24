"""ViewSets para operações de empréstimos e parcelas."""
from __future__ import annotations

from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional

from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from iabank.core.exceptions import TenantIsolationViolation
from iabank.core.logging import get_logger, log_business_event
from iabank.core.models import Tenant
from iabank.core.views import ApiResponseMixin
from iabank.finance.models import (
    BankAccount,
    PaymentCategory,
    PaymentCategoryType,
    FinancialTransaction,
    TransactionStatus as FinanceTransactionStatus,
    TransactionType as FinanceTransactionType,
)
from iabank.finance.serializers import (
    FinancialTransactionOutputSerializer,
    FinancialTransactionSerializer,
)
from iabank.operations.domain.entities import InstallmentEntity, LoanEntity, LoanStatus
from iabank.operations.domain.services import (
    DEFAULT_IOF_DAILY_RATE,
    DEFAULT_IOF_FIXED_RATE,
    LoanService,
)
from iabank.operations.models import Installment, InstallmentStatus, Loan
from iabank.operations.serializers import (
    InstallmentPaymentSerializer,
    LoanCancellationSerializer,
    LoanCreateSerializer,
    LoanInstallmentOutputSerializer,
    LoanOutputSerializer,
    LoanUpdateSerializer,
)


logger = get_logger(__name__)


def _resolve_tenant_id(request: Request) -> uuid.UUID:
    tenant_id = getattr(request, "tenant_id", None)
    if tenant_id is None and getattr(request.user, "tenant_id", None) is not None:
        tenant_id = request.user.tenant_id
    if tenant_id is None:
        raise TenantIsolationViolation("Tenant context is required for loan operations")
    try:
        return uuid.UUID(str(tenant_id))
    except (TypeError, ValueError) as exc:
        raise TenantIsolationViolation("Invalid tenant identifier") from exc


def _get_tenant_settings(tenant_id: uuid.UUID) -> Dict[str, Any]:
    record = (
        Tenant.objects.filter(id=tenant_id)
        .values_list("settings", flat=True)
        .first()
    )
    if not record:
        return {}
    return dict(record)


class LoanViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    """ViewSet principal para operações com empréstimos."""

    queryset = Loan.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanOutputSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    filterset_fields = {
        "status": ["exact"],
        "customer_id": ["exact"],
        "consultant_id": ["exact"],
    }
    search_fields = ["notes"]
    ordering_fields = ["created_at", "contract_date", "principal_amount", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = _resolve_tenant_id(self.request)
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .select_related("customer", "consultant__user")
            .prefetch_related(Prefetch("installments", queryset=Installment.objects.order_by("sequence")))
            .order_by(*self.ordering)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return LoanCreateSerializer
        if self.action in {"update", "partial_update"}:
            return LoanUpdateSerializer
        return LoanOutputSerializer

    def get_serializer_context(self) -> Dict[str, Any]:
        context = super().get_serializer_context()
        context.setdefault("request", self.request)
        return context

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = LoanOutputSerializer(
            page if page is not None else queryset,
            many=True,
            context=self.get_serializer_context(),
        )
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        data = serializer.data
        if page is not None:
            return self._success(data, meta=meta)
        return self._success(data, meta=meta)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        output = LoanOutputSerializer(loan, context=self.get_serializer_context())

        log_business_event(
            event_type="business",
            entity_type="loan",
            entity_id=str(loan.id),
            action="loan_created",
            tenant_id=str(loan.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(
            output.data,
            status_code=status.HTTP_201_CREATED,
            meta={"message": "Empréstimo criado com sucesso."},
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        loan = serializer.save()
        output = LoanOutputSerializer(loan, context=self.get_serializer_context())

        log_business_event(
            event_type="business",
            entity_type="loan",
            entity_id=str(loan.id),
            action="loan_updated",
            tenant_id=str(loan.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(output.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request: Request, pk: str = None) -> Response:
        loan = self.get_object()
        entity = LoanEntity.model_validate(loan)
        try:
            updated_entity = LoanService.approve(entity)
        except LoanStatusTransitionError as exc:
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        loan.status = updated_entity.status.value
        loan.save(update_fields=["status", "updated_at"])

        output = LoanOutputSerializer(loan, context=self.get_serializer_context())
        log_business_event(
            event_type="business",
            entity_type="loan",
            entity_id=str(loan.id),
            action="loan_approved",
            tenant_id=str(loan.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )
        return self._success(output.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk: str = None) -> Response:
        loan = self.get_object()
        serializer = LoanCancellationSerializer(data=request.data, context={"loan": loan})
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        output = LoanOutputSerializer(updated, context=self.get_serializer_context())
        log_business_event(
            event_type="business",
            entity_type="loan",
            entity_id=str(updated.id),
            action="loan_cancelled",
            tenant_id=str(updated.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )
        return self._success(output.data)

    @action(detail=True, methods=["get"], url_path="installments")
    def installments(self, request: Request, pk: str = None) -> Response:
        loan = self.get_object()
        installments_qs = loan.installments.order_by("sequence")
        serializer = LoanInstallmentOutputSerializer(
            installments_qs,
            many=True,
            context=self.get_serializer_context(),
        )
        return self._success(serializer.data)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request: Request, pk: str = None) -> Response:
        loan = self.get_object()
        history_records = list(loan.history.all().order_by("history_date", "history_id"))
        response: List[Dict[str, Any]] = []
        previous = None
        for record in history_records:
            changes: Dict[str, Any] = {}
            if previous is not None:
                diff = record.diff_against(previous)
                for delta in diff.changes:
                    changes[delta.field] = delta.new
            else:
                changes["status"] = record.status
            response.append(
                {
                    "history_id": str(record.history_id),
                    "history_date": record.history_date.isoformat() if record.history_date else None,
                    "history_type": _normalize_history_type(record.history_type),
                    "changes": changes,
                }
            )
            previous = record
        return self._success(response)

    @action(detail=True, methods=["get"], url_path="regulatory-validation")
    def regulatory_validation(self, request: Request, pk: str = None) -> Response:
        loan = self.get_object()
        entity = LoanEntity.model_validate(loan)
        tenant_id = _resolve_tenant_id(request)
        settings_dict = _get_tenant_settings(tenant_id)
        max_interest_rate = settings_dict.get("max_interest_rate")
        if max_interest_rate is not None:
            try:
                max_interest_rate = Decimal(str(max_interest_rate))
            except Exception:  # pragma: no cover - defensive
                max_interest_rate = None
        snapshot = LoanService.regulatory_snapshot(
            entity,
            max_interest_rate=max_interest_rate,
            iof_fixed_rate=DEFAULT_IOF_FIXED_RATE,
            iof_daily_rate=DEFAULT_IOF_DAILY_RATE,
            reference_date=timezone.localdate(),
        )
        return self._success(snapshot)


class InstallmentViewSet(ApiResponseMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet para operações diretas sobre parcelas."""

    queryset = Installment.objects.select_related("loan", "loan__customer")
    serializer_class = LoanInstallmentOutputSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        tenant_id = _resolve_tenant_id(self.request)
        return super().get_queryset().filter(tenant_id=tenant_id).order_by("sequence")

    @action(detail=True, methods=["post"], url_path="payments")
    def register_payment(self, request: Request, pk: str = None) -> Response:
        installment = self.get_object()
        serializer = InstallmentPaymentSerializer(
            data=request.data,
            context={"installment": installment},
        )
        serializer.is_valid(raise_exception=True)
        updated_installment = serializer.save()

        installment_output = LoanInstallmentOutputSerializer(
            updated_installment,
            context=self.get_serializer_context(),
        )

        transaction_instance = self._create_financial_transaction(
            installment=updated_installment,
            amount=serializer.validated_data["amount"],
            payment_date=serializer.validated_data["payment_date"],
            bank_account_id=serializer.validated_data.get("bank_account_id"),
            request=request,
        )
        transaction_payload = FinancialTransactionOutputSerializer(
            transaction_instance,
            context=self.get_serializer_context(),
        ).data

        log_business_event(
            event_type="business",
            entity_type="installment",
            entity_id=str(updated_installment.id),
            action="installment_payment_registered",
            tenant_id=str(updated_installment.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(
            {
                "installment": installment_output.data,
                "transaction": transaction_payload,
            },
            meta={"message": "Pagamento registrado com sucesso."},
        )

    def _create_financial_transaction(
        self,
        *,
        installment: Installment,
        amount: Decimal,
        payment_date: Any,
        bank_account_id: uuid.UUID | str | None,
        request: Request,
    ) -> FinancialTransaction:
        tenant_uuid = uuid.UUID(str(installment.tenant_id))

        account_id = bank_account_id or self._resolve_default_bank_account(tenant_uuid)
        if account_id is None:
            raise DRFValidationError({"bank_account_id": ["Conta bancária é obrigatória para registrar o pagamento."]})

        if not isinstance(account_id, uuid.UUID):
            account_id = uuid.UUID(str(account_id))

        category = self._ensure_income_category(tenant_uuid)
        description = f"Pagamento parcela {installment.sequence} do empréstimo {installment.loan_id}"

        serializer = FinancialTransactionSerializer(
            data={
                "bank_account_id": str(account_id),
                "type": FinanceTransactionType.INCOME.value,
                "category_id": str(category.id),
                "amount": amount,
                "description": description,
                "reference_date": payment_date,
                "payment_date": payment_date,
                "status": FinanceTransactionStatus.PAID.value,
                "installment_id": str(installment.id),
            },
            context={"request": request, "tenant_id": tenant_uuid},
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def _resolve_default_bank_account(self, tenant_id: uuid.UUID) -> Optional[uuid.UUID]:
        account = (
            BankAccount.objects.filter(tenant_id=tenant_id, is_main=True)
            .values_list("id", flat=True)
            .first()
        )
        return uuid.UUID(str(account)) if account else None

    def _ensure_income_category(self, tenant_id: uuid.UUID) -> PaymentCategory:
        category, created = PaymentCategory.objects.get_or_create(
            tenant_id=tenant_id,
            name="Receitas de Empréstimos",
            defaults={"type": PaymentCategoryType.INCOME, "is_active": True},
        )
        if not created and category.type not in {PaymentCategoryType.INCOME, PaymentCategoryType.BOTH}:
            category.type = PaymentCategoryType.INCOME
            category.is_active = True
            category.save(update_fields=["type", "is_active", "updated_at"])
        return category


def _normalize_history_type(history_type: str) -> str:
    mapping = {
        "+": "CREATE",
        "~": "UPDATE",
        "-": "DELETE",
    }
    return mapping.get(history_type, history_type.upper())


__all__ = ["LoanViewSet", "InstallmentViewSet"]



