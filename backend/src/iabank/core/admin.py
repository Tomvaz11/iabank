"""
Configuração do Django Admin para o app Core.

Define interfaces administrativas para os modelos Tenant e User,
facilitando a gestão de dados através do painel de administração.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Interface administrativa para o modelo Tenant."""
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Interface administrativa customizada para o modelo User."""
    list_display = ['username', 'email', 'first_name', 'last_name', 'tenant', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'tenant', 'is_tenant_admin']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações do Tenant', {
            'fields': ('tenant', 'phone', 'is_tenant_admin')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações do Tenant', {
            'fields': ('tenant', 'phone', 'is_tenant_admin')
        }),
    )