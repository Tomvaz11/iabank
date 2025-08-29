"""
Modelos base do app core do IABANK.

Este módulo contém os modelos fundamentais para suporte multi-tenant da
plataforma IABANK, incluindo o modelo Tenant e o modelo abstrato BaseTenantModel
para garantir isolamento de dados entre diferentes inquilinos (tenants) do sistema.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """
    Modelo que representa um inquilino (tenant) no sistema multi-tenant do IABANK.

    Cada tenant representa uma instância isolada da aplicação, permitindo que
    múltiplas organizações utilizem o sistema de forma compartilhada, mas com
    dados completamente segregados.
    """
    name = models.CharField(
        max_length=255,
        help_text="Nome do tenant/organização"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de criação do tenant"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização do tenant"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se o tenant está ativo no sistema"
    )

    class Meta:
        db_table = 'core_tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Modelo de usuário customizado que estende o AbstractUser do Django.

    Inclui associação obrigatória com um tenant para garantir o isolamento
    de usuários por organização no sistema multi-tenant.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        help_text="Tenant ao qual este usuário pertence"
    )

    class Meta:
        db_table = 'core_user'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.username} ({self.tenant.name})"


class BaseTenantModel(models.Model):
    """
    Modelo abstrato base para garantir que todos os dados sejam vinculados a um tenant.

    Este modelo deve ser usado como classe base para todos os modelos de negócio
    da aplicação, garantindo que os dados sejam sempre associados a um tenant
    específico e incluindo timestamps padrão de auditoria.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text="Tenant proprietário deste registro"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data e hora de criação do registro"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data e hora da última atualização do registro"
    )

    class Meta:
        abstract = True
