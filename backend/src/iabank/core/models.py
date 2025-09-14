"""
Core models para IABANK.
Models base para multi-tenancy e auditoria.
"""
import uuid
from typing import Any, Dict

from django.db import models
from simple_history.models import HistoricalRecords


class BaseTenantModel(models.Model):
    """
    Model base para multi-tenancy com auditoria automática.

    Todos os models do IABANK devem herdar desta classe para:
    - Garantir isolamento por tenant_id
    - Ter auditoria automática com django-simple-history
    - Campos padrão (created_at, updated_at)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único universal",
    )

    tenant_id = models.UUIDField(
        help_text="ID do tenant para isolamento de dados",
        db_index=True,
        null=True,  # Temporário para migration
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data/hora de criação do registro",
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Data/hora da última atualização",
        db_index=True,
    )

    # Auditoria automática com django-simple-history
    history = HistoricalRecords(
        inherit=True,
        excluded_fields=["updated_at"],  # updated_at é redundante no histórico
        history_id_field=models.UUIDField(default=uuid.uuid4),
        custom_model_name=lambda x: f"Historical{x}",
    )

    class Meta:
        abstract = True
        # Índices compostos obrigatórios com tenant_id primeiro
        indexes = [
            models.Index(
                fields=["tenant_id", "created_at"],
                name="%(app_label)s_%(class)s_tenant_created_idx",
            ),
            models.Index(
                fields=["tenant_id", "updated_at"],
                name="%(app_label)s_%(class)s_tenant_updated_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Override do save para validação de tenant_id.

        Raises:
            ValueError: Se tenant_id não foi informado
        """
        if not self.tenant_id:
            raise ValueError("tenant_id é obrigatório para todos os models")

        super().save(*args, **kwargs)

    def get_audit_fields(self) -> Dict[str, Any]:
        """
        Retorna campos para auditoria estruturada.

        Returns:
            dict: Campos relevantes para logs de auditoria
        """
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "model": self.__class__.__name__,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __str__(self) -> str:
        """String representation padrão."""
        return f"{self.__class__.__name__}({self.id})"


class Tenant(BaseTenantModel):
    """
    Model para empresas clientes da plataforma.

    Cada tenant representa uma empresa que usa o IABANK para
    gerenciar empréstimos. Isolamento completo de dados.
    """

    name = models.CharField(
        max_length=200,
        help_text="Nome da empresa",
    )

    cnpj = models.CharField(
        max_length=18,  # Formatado: 00.000.000/0000-00
        unique=True,
        help_text="CNPJ da empresa (formatado)",
        db_index=True,
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Tenant ativo na plataforma",
        db_index=True,
    )

    created_by = models.CharField(
        max_length=200,
        help_text="Usuário que criou o tenant",
        blank=True,
    )

    # Configurações específicas do tenant
    settings = models.JSONField(
        default=dict,
        help_text="Configurações específicas do tenant (taxa máxima, etc)",
    )

    class Meta:
        db_table = "core_tenants"
        indexes = [
            models.Index(fields=["cnpj"], name="core_tenants_cnpj_idx"),
            models.Index(fields=["is_active"], name="core_tenants_active_idx"),
        ]

    def save(self, *args, **kwargs):
        """Override para auto-definir tenant_id como próprio id."""
        if not self.tenant_id:
            # Para o model Tenant, tenant_id é o próprio id
            self.tenant_id = self.id or uuid.uuid4()
            if not self.id:
                self.id = self.tenant_id

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.cnpj})"