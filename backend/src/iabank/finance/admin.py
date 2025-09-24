"""Admin do módulo financeiro com filtragem automática por tenant."""
from __future__ import annotations

from django.contrib import admin

from iabank.core.admin import TenantScopedAdminMixin

from .models import (
    BankAccount,
    CostCenter,
    FinancialTransaction,
    PaymentCategory,
    Supplier,
)


@admin.register(BankAccount)
class BankAccountAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para contas bancárias."""

    list_display = (
        "bank_code",
        "bank_name",
        "account_type",
        "balance",
        "is_active",
        "is_main",
    )
    list_filter = ("account_type", "is_active", "is_main")
    search_fields = ("bank_code", "bank_name")
    ordering = ("bank_code",)
    readonly_fields = (
        "tenant_id",
        "account_identifier_hash",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Banco",
            {"fields": ("bank_code", "bank_name", "account_type")},
        ),
        (
            "Identificação",
            {"fields": ("agency", "account_number", "account_identifier_hash")},
        ),
        (
            "Status",
            {"fields": ("balance", "is_active", "is_main")},
        ),
        ("Metadados", {"fields": ("tenant_id", "created_at", "updated_at")}),
    )


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para categorias de pagamento."""

    list_display = ("name", "type", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)
    readonly_fields = ("tenant_id",)


@admin.register(CostCenter)
class CostCenterAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para centros de custo."""

    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    readonly_fields = ("tenant_id",)


@admin.register(Supplier)
class SupplierAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para fornecedores."""

    list_display = (
        "name",
        "document_type",
        "document_hash",
        "email",
        "is_active",
    )
    list_filter = ("document_type", "is_active")
    search_fields = ("document_hash",)
    readonly_fields = ("tenant_id", "document_hash")


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para transações financeiras."""

    list_display = (
        "description",
        "type",
        "amount",
        "status",
        "reference_date",
        "bank_account",
    )
    list_filter = ("type", "status", "reference_date")
    search_fields = (
        "description",
        "document_number",
        "bank_account__bank_code",
        "supplier__document_hash",
    )
    ordering = ("-reference_date",)
    readonly_fields = ("tenant_id", "created_at", "updated_at")
    fieldsets = (
        (
            "Classificação",
            {
                "fields": (
                    "type",
                    "category",
                    "cost_center",
                    "supplier",
                    "installment",
                )
            },
        ),
        (
            "Financeiro",
            {
                "fields": (
                    "bank_account",
                    "amount",
                    "description",
                    "document_number",
                )
            },
        ),
        (
            "Datas",
            {
                "fields": (
                    "reference_date",
                    "due_date",
                    "payment_date",
                    "status",
                )
            },
        ),
        ("Metadados", {"fields": ("tenant_id", "created_at", "updated_at")}),
    )


__all__ = [
    "BankAccountAdmin",
    "PaymentCategoryAdmin",
    "CostCenterAdmin",
    "SupplierAdmin",
    "FinancialTransactionAdmin",
]
