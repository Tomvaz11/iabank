"""
Configuração do Django Admin para o app Customers.

Define interfaces administrativas para facilitar a gestão
de clientes através do painel de administração.
"""

from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Interface administrativa para o modelo Customer."""
    
    list_display = [
        'name', 
        'document_number', 
        'email', 
        'primary_contact',
        'city', 
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'is_active', 
        'state', 
        'city',
        'created_at',
        'tenant'
    ]
    
    search_fields = [
        'name', 
        'document_number', 
        'email', 
        'phone', 
        'mobile_phone'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('name', 'document_number', 'birth_date')
        }),
        ('Contato', {
            'fields': ('email', 'phone', 'mobile_phone')
        }),
        ('Endereço', {
            'fields': (
                'zip_code', 'street', 'number', 'complement',
                'neighborhood', 'city', 'state'
            )
        }),
        ('Configurações', {
            'fields': ('tenant', 'is_active', 'notes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def primary_contact(self, obj):
        """Exibe o contato principal na lista."""
        return obj.primary_contact
    primary_contact.short_description = "Contato principal"