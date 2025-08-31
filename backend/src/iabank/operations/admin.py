"""
Configuração do Django Admin para o app Operations.

Define interfaces administrativas para gestão de consultores,
empréstimos e parcelas através do painel de administração.
"""

from django.contrib import admin
from .models import Consultant, Loan, Installment


@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    """Interface administrativa para o modelo Consultant."""
    
    list_display = ['user', 'balance', 'is_active', 'tenant', 'created_at']
    list_filter = ['is_active', 'tenant', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'tenant', 'balance', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class InstallmentInline(admin.TabularInline):
    """Inline para parcelas dentro da edição de empréstimo."""
    
    model = Installment
    extra = 0
    readonly_fields = ['installment_number', 'amount_due', 'remaining_amount']
    fields = [
        'installment_number', 'due_date', 'amount_due', 
        'amount_paid', 'payment_date', 'status'
    ]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Interface administrativa para o modelo Loan."""
    
    list_display = [
        'id', 'customer', 'consultant', 'principal_amount',
        'status', 'contract_date', 'number_of_installments'
    ]
    
    list_filter = ['status', 'consultant', 'contract_date', 'tenant']
    
    search_fields = [
        'customer__name', 'customer__document_number',
        'consultant__user__username'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'total_amount', 'installment_amount']
    inlines = [InstallmentInline]
    
    fieldsets = (
        ('Informações do Contrato', {
            'fields': (
                'customer', 'consultant', 'tenant',
                'contract_date', 'first_installment_date'
            )
        }),
        ('Dados Financeiros', {
            'fields': (
                'principal_amount', 'interest_rate', 'number_of_installments',
                'total_amount', 'installment_amount'
            )
        }),
        ('Status e Observações', {
            'fields': ('status', 'notes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    """Interface administrativa para o modelo Installment."""
    
    list_display = [
        'loan', 'installment_number', 'due_date',
        'amount_due', 'amount_paid', 'remaining_amount', 'status'
    ]
    
    list_filter = ['status', 'due_date', 'loan__status', 'tenant']
    
    search_fields = [
        'loan__customer__name', 'loan__customer__document_number',
        'loan__id'
    ]
    
    readonly_fields = ['remaining_amount', 'is_overdue', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações da Parcela', {
            'fields': ('loan', 'installment_number', 'due_date', 'tenant')
        }),
        ('Valores', {
            'fields': (
                'amount_due', 'amount_paid', 'remaining_amount'
            )
        }),
        ('Pagamento', {
            'fields': ('payment_date', 'status', 'is_overdue')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )