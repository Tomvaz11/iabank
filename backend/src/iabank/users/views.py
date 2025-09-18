"""ViewSets para autenticação e gestão de usuários."""
from __future__ import annotations

import uuid
from typing import Optional, Type

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from iabank.core.exceptions import TenantIsolationViolation
from iabank.core.jwt_views import TokenObtainPairView, TokenRefreshView
from iabank.core.logging import get_logger, log_business_event
from iabank.core.views import ApiResponseMixin
from iabank.users.domain.entities import UserEntity
from iabank.users.domain.services import InvalidRoleError, UserService
from iabank.users.models import User
from iabank.users.serializers import (
    UserCreateSerializer,
    UserOutputSerializer,
    UserUpdateSerializer,
)


logger = get_logger(__name__)


class AuthViewSet(ApiResponseMixin, viewsets.ViewSet):
    """Endpoints de autenticação baseados em JWT."""

    permission_classes = [permissions.AllowAny]

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request: Request, *args, **kwargs) -> Response:
        """Delegação para o fluxo customizado de emissão de tokens."""

        logger.info("Login attempt", email=request.data.get("email"))
        return self._dispatch(TokenObtainPairView, request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request: Request, *args, **kwargs) -> Response:
        """Gera novo access token a partir de um refresh token válido."""

        return self._dispatch(TokenRefreshView, request, *args, **kwargs)

    def _dispatch(
        self,
        view_cls: Type,
        request: Request,
        *args,
        **kwargs,
    ) -> Response:
        """Encaminha requisição para uma APIView já existente."""

        view = view_cls.as_view()
        return view(request._request, *args, **kwargs)


class UserViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    """ViewSet para gestão de usuários multi-tenant."""

    queryset = User.objects.all()
    serializer_class = UserOutputSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "patch", "delete"]
    filterset_fields = {"role": ["exact"], "is_active": ["exact"]}
    search_fields = ["email", "first_name", "last_name", "username"]
    ordering_fields = ["first_name", "last_name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self._get_tenant_id()
        base_queryset = super().get_queryset()
        return base_queryset.filter(tenant_id=tenant_id).order_by(*self.ordering)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in {"update", "partial_update"}:
            return UserUpdateSerializer
        return UserOutputSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            meta = {"pagination": self._pagination_meta()}
            return self._success(serializer.data, meta=meta)

        serializer = self.get_serializer(queryset, many=True)
        meta = {"pagination": self._pagination_meta(queryset)}
        return self._success(serializer.data, meta=meta)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        output = UserOutputSerializer(user, context=self.get_serializer_context())
        tenant_id = self._get_tenant_id()
        actor_id = str(request.user.id) if request.user.is_authenticated else None
        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(user.id),
            action="user_created",
            tenant_id=str(tenant_id),
            user_id=actor_id,
        )

        return self._success(
            output.data,
            status_code=status.HTTP_201_CREATED,
            meta={"message": "Usuário criado com sucesso."},
        )

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self._success(serializer.data)

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        output = UserOutputSerializer(user, context=self.get_serializer_context())
        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(user.id),
            action="user_updated",
            tenant_id=str(self._get_tenant_id()),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )
        return self._success(output.data)

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        entity = UserEntity.model_validate(instance)

        try:
            updated = UserService.deactivate(entity)
        except InvalidRoleError as exc:
            raise DRFValidationError({"role": [str(exc)]}) from exc

        instance.is_active = updated.is_active
        instance.save(update_fields=["is_active", "updated_at"])

        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(instance.id),
            action="user_deactivated",
            tenant_id=str(self._get_tenant_id()),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_tenant_id(self) -> uuid.UUID:
        tenant_id = getattr(self.request, "tenant_id", None)
        if not tenant_id:
            logger.error("Tenant context missing in request", path=self.request.path)
            raise TenantIsolationViolation("Tenant context is required for user operations")
        try:
            return uuid.UUID(str(tenant_id))
        except (TypeError, ValueError) as exc:
            raise TenantIsolationViolation("Invalid tenant identifier") from exc
