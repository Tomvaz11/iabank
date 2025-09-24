"""Configuração do Django admin com suporte multi-tenant."""
from __future__ import annotations

import uuid
from typing import Optional

from django.contrib import admin
from django.db.models import Model

from .models import BaseTenantModel, Tenant


class TenantScopedAdminMixin:
    """Aplica filtragem automática por tenant para ModelAdmins."""

    tenant_field: str = "tenant_id"

    def get_queryset(self, request):  # type: ignore[override]
        queryset = super().get_queryset(request)
        tenant_id = self._get_request_tenant_id(request)
        if tenant_id is None or request.user.is_superuser:
            return queryset
        return queryset.filter(**{self.tenant_field: tenant_id})

    def has_view_permission(self, request, obj: Optional[Model] = None):  # type: ignore[override]
        has_perm = super().has_view_permission(request, obj=obj)
        return has_perm and self._object_belongs_to_tenant(request, obj)

    def has_change_permission(self, request, obj: Optional[Model] = None):  # type: ignore[override]
        has_perm = super().has_change_permission(request, obj=obj)
        return has_perm and self._object_belongs_to_tenant(request, obj)

    def has_delete_permission(self, request, obj: Optional[Model] = None):  # type: ignore[override]
        has_perm = super().has_delete_permission(request, obj=obj)
        return has_perm and self._object_belongs_to_tenant(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):  # type: ignore[override]
        tenant_id = self._get_request_tenant_id(request)
        should_scope_fk = (
            tenant_id is not None
            and not request.user.is_superuser
            and db_field.remote_field
            and getattr(db_field.remote_field, "model", None)
        )
        if should_scope_fk:
            related_model = db_field.remote_field.model
            if isinstance(related_model, type) and issubclass(related_model, BaseTenantModel):
                kwargs["queryset"] = related_model.objects.filter(
                    **{self.tenant_field: tenant_id}
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):  # type: ignore[override]
        tenant_id = self._get_request_tenant_id(request)
        if tenant_id is not None and isinstance(obj, BaseTenantModel):
            obj.tenant_id = tenant_id
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):  # type: ignore[override]
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and self.tenant_field not in readonly:
            readonly.append(self.tenant_field)
        return tuple(readonly)

    def _object_belongs_to_tenant(self, request, obj: Optional[Model]) -> bool:
        if obj is None or request.user.is_superuser:
            return True
        tenant_id = self._get_request_tenant_id(request)
        if tenant_id is None:
            return False
        object_tenant = getattr(obj, self.tenant_field, None)
        if object_tenant is None:
            return False
        try:
            return uuid.UUID(str(object_tenant)) == tenant_id
        except (TypeError, ValueError, AttributeError):
            return False

    @staticmethod
    def _get_request_tenant_id(request) -> Optional[uuid.UUID]:
        raw_tenant = getattr(request, "tenant_id", None) or getattr(
            request.user, "tenant_id", None
        )
        if raw_tenant is None:
            return None
        try:
            return uuid.UUID(str(raw_tenant))
        except (TypeError, ValueError, AttributeError):
            return None


@admin.register(Tenant)
class TenantAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin do modelo Tenant com escopo multi-tenant."""

    list_display = (
        "name",
        "slug",
        "document_formatted",
        "domain",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "document", "domain")
    ordering = ("name",)
    readonly_fields = (
        "id",
        "tenant_id",
        "document_formatted",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        ("Identificação", {"fields": ("name", "slug", "document", "document_formatted")}),
        (
            "Contato",
            {"fields": ("domain", "contact_email", "phone_number")},
        ),
        ("Status", {"fields": ("is_active", "created_by")}),
        ("Configurações", {"fields": ("settings",)}),
        ("Metadados", {"fields": ("id", "tenant_id", "created_at", "updated_at")}),
    )


__all__ = ["TenantScopedAdminMixin", "TenantAdmin"]
