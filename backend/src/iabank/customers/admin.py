"""Admin do módulo de clientes com isolamento por tenant."""
from __future__ import annotations

from django.contrib import admin

from iabank.core.admin import TenantScopedAdminMixin

from .models import Address, Customer


@admin.register(Customer)
class CustomerAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para clientes."""

    list_display = (
        "name",
        "document_formatted",
        "email",
        "credit_score",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "document_type")
    search_fields = ("document_hash",)
    ordering = ("-created_at",)
    readonly_fields = (
        "tenant_id",
        "document_hash",
        "document_formatted",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Dados pessoais",
            {
                "fields": (
                    "name",
                    "email",
                    "phone",
                    "document_type",
                    "document",
                    "document_formatted",
                )
            },
        ),
        (
            "Informações financeiras",
            {"fields": ("monthly_income", "credit_score", "score_last_updated")},
        ),
        (
            "Metadados",
            {
                "fields": (
                    "tenant_id",
                    "document_hash",
                    "is_active",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Address)
class AddressAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para endereços de clientes."""

    list_display = (
        "customer",
        "type",
        "city",
        "state",
        "zipcode",
        "is_primary",
    )
    list_filter = ("type", "state", "is_primary")
    search_fields = ("customer__document_hash", "zipcode")
    readonly_fields = ("tenant_id",)


__all__ = ["CustomerAdmin", "AddressAdmin"]
