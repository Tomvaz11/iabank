"""
Configurações do Django Admin para o app core.

Este módulo contém as configurações de administração para os modelos Tenant e User,
permitindo gerenciamento através da interface administrativa do Django.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Tenant

User = get_user_model()


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Configuração do admin para o modelo Tenant."""

    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Informações de Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuração do admin para o modelo User customizado."""

    # Campos exibidos na listagem
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'tenant',
        'is_active', 'date_joined'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'tenant', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'tenant__name')
    ordering = ('username',)

    # Adiciona o campo tenant aos fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações do Tenant', {
            'fields': ('tenant',)
        }),
    )

    # Adiciona o campo tenant ao formulário de criação
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações do Tenant', {
            'fields': ('tenant',)
        }),
    )
