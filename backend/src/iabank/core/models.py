from django.db import models
import uuid


class BaseTenantModel(models.Model):
    """
    Abstract base model que implementa multi-tenancy obrigatório.
    Todos os models do sistema devem herdar desta classe.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            # tenant_id sempre como primeira coluna do índice
            models.Index(fields=['tenant_id', 'created_at']),
            models.Index(fields=['tenant_id', 'updated_at']),
        ]


class Tenant(models.Model):
    """
    Modelo para empresas clientes da plataforma (isolamento de dados).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=14, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name