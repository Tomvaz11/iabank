"""
Configuração do Django Admin para o app Finance.

Define interfaces administrativas para gestão de entidades
financeiras através do painel de administração.
"""

from django.contrib import admin
from .models import BankAccount, PaymentCategory, CostCenter, Supplier, FinancialTransaction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Interface administrativa para contas bancárias."""
    
    list_display = ['name', 'bank_name', 'account_number', 'current_balance', 'is_active']
    list_filter = ['is_active', 'bank_name', 'tenant']
    search_fields = ['name', 'bank_name', 'account_number']
    readonly_fields = ['current_balance', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Conta', {
            'fields': ('name', 'bank_name', 'agency', 'account_number', 'tenant')
        }),
        ('Saldos', {
            'fields': ('initial_balance', 'current_balance')
        }),
        ('Configurações', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    """Interface administrativa para categorias de pagamento."""
    
    list_display = ['name', 'is_active', 'tenant', 'created_at']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    """Interface administrativa para centros de custo."""
    
    list_display = ['code', 'name', 'is_active', 'tenant']
    list_filter = ['is_active', 'tenant']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('code', 'name', 'tenant', 'description')
        }),
        ('Configurações', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    """Interface administrativa para fornecedores."""
    
    list_display = ['name', 'document_number', 'email', 'phone', 'is_active']
    list_filter = ['is_active', 'tenant']
    search_fields = ['name', 'document_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'document_number', 'tenant')
        }),
        ('Contato', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Configurações', {
            'fields': ('is_active',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    """Interface administrativa para transações financeiras."""
    
    list_display = [
        'description', 'amount', 'type', 'transaction_date',
        'is_paid', 'status_display', 'bank_account'
    ]
    
    list_filter = [
        'type', 'is_paid', 'transaction_date', 'category',
        'cost_center', 'bank_account', 'tenant'
    ]
    
    search_fields = [
        'description', 'supplier__name', 'category__name',
        'cost_center__name'
    ]
    
    readonly_fields = ['status_display', 'is_overdue', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Transação', {
            'fields': (
                'description', 'type', 'amount', 'tenant',
                'transaction_date', 'due_date'
            )
        }),
        ('Pagamento', {
            'fields': ('is_paid', 'payment_date', 'status_display', 'is_overdue')
        }),
        ('Classificações', {
            'fields': (
                'bank_account', 'category', 'cost_center',
                'supplier', 'installment'
            )
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def status_display(self, obj):
        """Exibe o status da transação na lista."""
        return obj.status_display
    status_display.short_description = "Status"