"""ViewSets e relatórios do módulo financeiro."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from iabank.core.exceptions import TenantIsolationViolation
from iabank.core.logging import get_logger, log_business_event
from iabank.core.views import ApiResponseMixin
from iabank.finance.models import (
    BankAccount,
    CostCenter,
    FinancialTransaction,
    PaymentCategory,
    Supplier,
    TransactionStatus as ModelTransactionStatus,
    TransactionType as ModelTransactionType,
)
from iabank.finance.serializers import (
    BankAccountSerializer,
    CostCenterSerializer,
    FinancialTransactionOutputSerializer,
    FinancialTransactionSerializer,
    PaymentCategorySerializer,
    SupplierSerializer,
)
from iabank.operations.models import Loan, LoanStatus


logger = get_logger(__name__)


def _resolve_tenant_id(request: Request) -> uuid.UUID:
    tenant_candidate = getattr(request, "tenant_id", None)
    if tenant_candidate is None and getattr(request.user, "tenant_id", None) is not None:
        tenant_candidate = request.user.tenant_id
    if tenant_candidate is None:
        logger.error("Tenant context missing", path=request.path)
        raise TenantIsolationViolation("Tenant context is required for finance operations")
    try:
        return uuid.UUID(str(tenant_candidate))
    except (TypeError, ValueError) as exc:
        raise TenantIsolationViolation("Invalid tenant identifier") from exc


class TenantScopedMixin:
    """Mixin para adicionar tenant_id ao contexto do serializer."""

    def get_serializer_context(self) -> Dict[str, Any]:  # type: ignore[override]
        context = super().get_serializer_context()
        try:
            context.setdefault("tenant_id", _resolve_tenant_id(self.request))
        except TenantIsolationViolation:
            pass
        return context


class BankAccountViewSet(TenantScopedMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """CRUD de contas bancárias corporativas do tenant."""

    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {
        "account_type": ["exact"],
        "is_active": ["exact"],
        "bank_code": ["exact"],
    }
    ordering_fields = ["bank_code", "bank_name", "created_at"]
    ordering = ["bank_code"]

    def get_queryset(self):  # type: ignore[override]
        tenant_id = _resolve_tenant_id(self.request)
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .order_by(*self.ordering)
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        output = self.get_serializer(account)

        log_business_event(
            event_type="business",
            entity_type="bank_account",
            entity_id=str(account.id),
            action="bank_account_created",
            tenant_id=str(account.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(
            output.data,
            status_code=status.HTTP_201_CREATED,
            meta={"message": "Conta bancária criada com sucesso."},
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        account = serializer.save()
        output = self.get_serializer(account)

        log_business_event(
            event_type="business",
            entity_type="bank_account",
            entity_id=str(account.id),
            action="bank_account_updated",
            tenant_id=str(account.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(output.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        instance = self.get_object()
        serializer = self.get_serializer(instance, data={"is_active": False}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_business_event(
            event_type="business",
            entity_type="bank_account",
            entity_id=str(instance.id),
            action="bank_account_deactivated",
            tenant_id=str(instance.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class PaymentCategoryViewSet(TenantScopedMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """CRUD de categorias financeiras."""

    queryset = PaymentCategory.objects.all()
    serializer_class = PaymentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {"type": ["exact"], "is_active": ["exact"]}
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):  # type: ignore[override]
        tenant_id = _resolve_tenant_id(self.request)
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .order_by(*self.ordering)
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def perform_destroy(self, instance: PaymentCategory) -> None:  # type: ignore[override]
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class CostCenterViewSet(TenantScopedMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """CRUD de centros de custo."""

    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {"is_active": ["exact"], "code": ["exact"]}
    ordering_fields = ["code", "name", "created_at"]
    ordering = ["code"]

    def get_queryset(self):  # type: ignore[override]
        tenant_id = _resolve_tenant_id(self.request)
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .order_by(*self.ordering)
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def perform_destroy(self, instance: CostCenter) -> None:  # type: ignore[override]
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class SupplierViewSet(TenantScopedMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """CRUD de fornecedores."""

    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {"is_active": ["exact"], "document_type": ["exact"]}
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):  # type: ignore[override]
        tenant_id = _resolve_tenant_id(self.request)
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .order_by(*self.ordering)
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def perform_destroy(self, instance: Supplier) -> None:  # type: ignore[override]
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class FinancialTransactionViewSet(TenantScopedMixin, ApiResponseMixin, viewsets.ModelViewSet):
    """CRUD de transações financeiras com filtros avançados."""

    queryset = FinancialTransaction.objects.select_related(
        "bank_account",
        "category",
        "cost_center",
        "supplier",
        "installment",
    )
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {
        "type": ["exact"],
        "status": ["exact"],
        "bank_account_id": ["exact"],
        "category_id": ["exact"],
    }
    ordering_fields = ["reference_date", "amount", "created_at"]
    ordering = ["-reference_date"]

    def get_queryset(self):  # type: ignore[override]
        tenant_id = _resolve_tenant_id(self.request)
        queryset = (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
        )

        params = self.request.query_params
        start_date = params.get("start_date")
        if start_date:
            queryset = queryset.filter(reference_date__gte=start_date)
        end_date = params.get("end_date")
        if end_date:
            queryset = queryset.filter(reference_date__lte=end_date)
        loan_id = params.get("loan_id")
        if loan_id:
            try:
                loan_uuid = uuid.UUID(str(loan_id))
            except (TypeError, ValueError):
                raise DRFValidationError({"loan_id": ["Identificador de empréstimo inválido."]})
            queryset = queryset.filter(installment__loan_id=loan_uuid)
        return queryset.order_by(*self.ordering)

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in {"list", "retrieve"}:
            return FinancialTransactionOutputSerializer
        return FinancialTransactionSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        meta = {"pagination": self._pagination_meta() if page is not None else self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_record = serializer.save()
        output = FinancialTransactionOutputSerializer(transaction_record, context=self.get_serializer_context())

        log_business_event(
            event_type="business",
            entity_type="financial_transaction",
            entity_id=str(transaction_record.id),
            action="financial_transaction_created",
            tenant_id=str(transaction_record.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(
            output.data,
            status_code=status.HTTP_201_CREATED,
            meta={"message": "Transação registrada com sucesso."},
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        output = FinancialTransactionOutputSerializer(record, context=self.get_serializer_context())

        log_business_event(
            event_type="business",
            entity_type="financial_transaction",
            entity_id=str(record.id),
            action="financial_transaction_updated",
            tenant_id=str(record.tenant_id),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return self._success(output.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class DashboardReportView(ApiResponseMixin, APIView):
    """Dashboard financeiro com métricas agregadas."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        tenant_id = _resolve_tenant_id(request)
        period_param = request.query_params.get("period", "30d").lower()
        days = self._resolve_period_days(period_param)
        today = timezone.localdate()
        since = today - timedelta(days=days - 1)

        loans_qs = Loan.objects.filter(tenant_id=tenant_id)
        total_loans = loans_qs.count()
        active_loans = loans_qs.filter(status=LoanStatus.ACTIVE).count()
        total_amount = loans_qs.aggregate(total=Sum("total_amount"))
        total_amount_value = total_amount.get("total") or Decimal("0")

        default_loans = loans_qs.filter(status=LoanStatus.COLLECTION).count()
        default_rate = (Decimal(default_loans) / Decimal(total_loans)).quantize(Decimal("0.0001")) if total_loans else Decimal("0")

        income_qs = FinancialTransaction.objects.filter(
            tenant_id=tenant_id,
            type=ModelTransactionType.INCOME,
            status=ModelTransactionStatus.PAID,
            reference_date__gte=since,
        )
        monthly_revenue = income_qs.aggregate(total=Sum("amount")).get("total") or Decimal("0")

        loans_by_status: Dict[str, int] = {
            record["status"]: record["total"]
            for record in loans_qs.values("status").annotate(total=Count("id"))
        }

        payments_trend = [
            {
                "date": item["reference_date"].isoformat(),
                "amount": item["total"],
            }
            for item in income_qs.values("reference_date").annotate(total=Sum("amount")).order_by("reference_date")
        ]

        data = {
            "total_active_loans": active_loans,
            "total_loan_amount": total_amount_value,
            "default_rate": default_rate,
            "monthly_revenue": monthly_revenue,
            "loans_by_status": loans_by_status,
            "payments_trend": payments_trend,
        }
        return self._success(data)

    @staticmethod
    def _resolve_period_days(value: str) -> int:
        mapping = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        if value not in mapping:
            raise DRFValidationError({"period": ["Período inválido. Use 7d, 30d, 90d ou 1y."]})
        return mapping[value]


class CashFlowReportView(ApiResponseMixin, APIView):
    """Relatório consolidado de fluxo de caixa."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:  # type: ignore[override]
        tenant_id = _resolve_tenant_id(request)
        start_date, end_date = self._parse_period(request)

        transactions = FinancialTransaction.objects.filter(
            tenant_id=tenant_id,
            status=ModelTransactionStatus.PAID,
            reference_date__gte=start_date,
            reference_date__lte=end_date,
        )

        income_total = transactions.filter(type=ModelTransactionType.INCOME).aggregate(total=Sum("amount")).get("total") or Decimal("0")
        expense_total = transactions.filter(type=ModelTransactionType.EXPENSE).aggregate(total=Sum("amount")).get("total") or Decimal("0")
        net_flow = income_total - expense_total

        daily_map: Dict[date, Dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expenses": Decimal("0")})
        for item in transactions.values("reference_date", "type").annotate(total=Sum("amount")):
            ref_date: date = item["reference_date"]
            total = item["total"] or Decimal("0")
            if item["type"] == ModelTransactionType.INCOME:
                daily_map[ref_date]["income"] += total
            else:
                daily_map[ref_date]["expenses"] += total

        daily_flow = [
            {
                "date": ref_date.isoformat(),
                "income": values["income"],
                "expenses": values["expenses"],
                "net": values["income"] - values["expenses"],
            }
            for ref_date, values in sorted(daily_map.items())
        ]

        data = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "income": income_total,
            "expenses": expense_total,
            "net_flow": net_flow,
            "daily_flow": daily_flow,
        }
        return self._success(data)

    @staticmethod
    def _parse_period(request: Request) -> tuple[date, date]:
        start_param = request.query_params.get("start_date")
        end_param = request.query_params.get("end_date")
        if not start_param or not end_param:
            raise DRFValidationError({"detail": ["start_date e end_date são obrigatórios."]})
        try:
            start_date = date.fromisoformat(start_param)
            end_date = date.fromisoformat(end_param)
        except ValueError as exc:
            raise DRFValidationError({"detail": ["Datas devem estar no formato YYYY-MM-DD."]}) from exc
        if start_date > end_date:
            raise DRFValidationError({"detail": ["start_date deve ser anterior ou igual a end_date."]})
        return start_date, end_date


__all__ = [
    "BankAccountViewSet",
    "PaymentCategoryViewSet",
    "CostCenterViewSet",
    "SupplierViewSet",
    "FinancialTransactionViewSet",
    "DashboardReportView",
    "CashFlowReportView",
]
