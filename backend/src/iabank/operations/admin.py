"""Admin do módulo de operações com escopo multi-tenant."""
from __future__ import annotations

from django.contrib import admin

from iabank.core.admin import TenantScopedAdminMixin

from .models import Installment, Loan


@admin.register(Loan)
class LoanAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para empréstimos."""

    list_display = (
        "id",
        "customer",
        "principal_amount",
        "interest_rate",
        "status",
        "contract_date",
        "regret_deadline",
    )
    list_filter = ("status", "contract_date")
    search_fields = ("id", "customer__document_hash", "consultant__user__email")
    ordering = ("-created_at",)
    readonly_fields = (
        "tenant_id",
        "regret_deadline",
        "version",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Relacionamentos",
            {"fields": ("customer", "consultant")},
        ),
        (
            "Valores",
            {
                "fields": (
                    "principal_amount",
                    "interest_rate",
                    "installments_count",
                    "iof_amount",
                    "cet_monthly",
                    "cet_yearly",
                    "total_amount",
                )
            },
        ),
        (
            "Datas",
            {"fields": ("contract_date", "first_due_date", "regret_deadline")},
        ),
        (
            "Status",
            {"fields": ("status", "notes", "version")},
        ),
        (
            "Metadados",
            {
                "fields": (
                    "tenant_id",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Installment)
class InstallmentAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para parcelas."""

    list_display = (
        "loan",
        "sequence",
        "due_date",
        "total_amount",
        "amount_paid",
        "status",
    )
    list_filter = ("status", "due_date")
    search_fields = ("loan__id",)
    ordering = ("loan", "sequence")
    readonly_fields = ("tenant_id",)


__all__ = ["LoanAdmin", "InstallmentAdmin"]
