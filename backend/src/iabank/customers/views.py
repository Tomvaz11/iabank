"""ViewSets para operações de clientes."""
from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from iabank.core.exceptions import TenantIsolationViolation
from iabank.core.logging import get_logger, log_business_event
from iabank.core.views import ApiResponseMixin
from iabank.customers.domain.entities import CustomerEntity
from iabank.customers.domain.services import CustomerService
from iabank.customers.models import Customer
from iabank.customers.serializers import (
    CreditAnalysisSerializer,
    CustomerCreateSerializer,
    CustomerOutputSerializer,
    CustomerUpdateSerializer,
)


logger = get_logger(__name__)


class CustomerViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    """ViewSet para CRUD de clientes com isolamento multi-tenant."""

    queryset = Customer.objects.all()
    serializer_class = CustomerOutputSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    filterset_fields = {
        "document_type": ["exact"],
        "is_active": ["exact"],
        "gender": ["exact"],
        "credit_score": ["gte", "lte"],
    }
    search_fields = ["name", "email"]
    ordering_fields = ["name", "created_at", "credit_score", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self._get_tenant_id()
        return (
            super()
            .get_queryset()
            .filter(tenant_id=tenant_id)
            .select_related()
            .prefetch_related("addresses")
            .order_by(*self.ordering)
        )

    def get_serializer_class(self):
        if self.action == "create":
            return CustomerCreateSerializer
        if self.action in {"update", "partial_update"}:
            return CustomerUpdateSerializer
        return CustomerOutputSerializer

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = CustomerOutputSerializer(page, many=True, context=self.get_serializer_context())
            meta = {"pagination": self._pagination_meta()}
            return self._success(serializer.data, meta=meta)

        serializer = CustomerOutputSerializer(queryset, many=True, context=self.get_serializer_context())
        meta = {"pagination": self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()

        output = CustomerOutputSerializer(customer, context=self.get_serializer_context())
        self._log_business_event(customer, action="customer_created")

        return self._success(
            output.data,
            status_code=status.HTTP_201_CREATED,
            meta={"message": "Cliente criado com sucesso."},
        )

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        serializer = CustomerOutputSerializer(instance, context=self.get_serializer_context())
        return self._success(serializer.data)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()

        output = CustomerOutputSerializer(customer, context=self.get_serializer_context())
        self._log_business_event(customer, action="customer_updated")
        return self._success(output.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance = self.get_object()
        entity = CustomerEntity.model_validate(instance)

        try:
            updated = CustomerService.deactivate(entity)
        except Exception as exc:  # pragma: no cover - fallback
            logger.exception("Failed to deactivate customer", customer_id=str(instance.id))
            raise DRFValidationError({"detail": ["Não foi possível desativar o cliente."]}) from exc

        instance.is_active = updated.is_active
        instance.save(update_fields=["is_active", "updated_at"])

        self._log_business_event(instance, action="customer_deactivated")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="credit-analysis")
    def credit_analysis(self, request: Request, pk: str = None) -> Response:
        customer = self.get_object()
        serializer = CreditAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        entity = CustomerEntity.model_validate(customer)
        updated_entity = CustomerService.update_credit_score(
            entity,
            credit_score=serializer.validated_data["new_score"],
            as_of=timezone.now(),
        )

        with transaction.atomic():
            customer.credit_score = updated_entity.credit_score
            customer.score_last_updated = updated_entity.score_last_updated
            customer.full_clean()
            customer.save(update_fields=["credit_score", "score_last_updated", "updated_at"])

        output = CustomerOutputSerializer(customer, context=self.get_serializer_context())
        self._log_business_event(
            customer,
            action="customer_credit_score_updated",
            extra={
                "analysis_reason": serializer.validated_data.get("analysis_reason"),
                "analyst_notes": serializer.validated_data.get("analyst_notes"),
            },
        )

        return self._success(
            output.data,
            meta={"message": "Score de crédito atualizado com sucesso."},
        )

    def _log_business_event(self, customer: Customer, *, action: str, extra: dict[str, Any] | None = None) -> None:
        context = {
            "event_type": "business",
            "entity_type": "customer",
            "entity_id": str(customer.id),
            "action": action,
            "tenant_id": str(customer.tenant_id),
            "user_id": str(self.request.user.id) if self.request.user.is_authenticated else None,
        }
        if extra:
            context.update(extra)
        log_business_event(**context)

    def _get_tenant_id(self) -> uuid.UUID:
        tenant_id = getattr(self.request, "tenant_id", None)
        if not tenant_id:
            tenant_id = getattr(self.request.user, "tenant_id", None)
        if not tenant_id:
            logger.error("Tenant context missing in request", path=self.request.path)
            raise TenantIsolationViolation("Tenant context is required for customer operations")
        try:
            return uuid.UUID(str(tenant_id))
        except (TypeError, ValueError) as exc:
            raise TenantIsolationViolation("Invalid tenant identifier") from exc
