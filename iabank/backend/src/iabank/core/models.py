"""
Modelos base do sistema IABANK.

Define os modelos fundamentais como Tenant, User e BaseTenantModel
que são utilizados por todos os outros apps para garantir isolamento
de dados multi-tenant e funcionalidades comuns.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class Tenant(models.Model):
    """
    Modelo que representa um inquilino (tenant) no sistema multi-tenant.
    Cada organização/empresa possui seu próprio tenant para isolamento de dados.
    """
    name = models.CharField(max_length=255, verbose_name="Nome")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Modelo de usuário customizado que extends AbstractUser do Django.
    Inclui associação com tenant para isolamento multi-tenant.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        verbose_name="Tenant"
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    is_tenant_admin = models.BooleanField(
        default=False,
        verbose_name="Administrador do Tenant"
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.tenant.name})"


class BaseTenantModel(models.Model):
    """
    Modelo abstrato base para garantir que todos os dados sejam vinculados a um tenant.
    Inclui campos comuns de auditoria (created_at, updated_at).
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        verbose_name="Tenant"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Validação para garantir que o tenant seja sempre definido
        if not self.tenant_id:
            raise ValueError("Tenant deve ser especificado para este modelo")
        super().save(*args, **kwargs)