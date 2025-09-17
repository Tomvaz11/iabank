"""
Core models para IABANK.
Models base para multi-tenancy e auditoria.
"""
import re
import uuid
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


def _default_tenant_settings() -> Dict[str, Any]:
    """Configuracoes padrao aplicadas a novos tenants."""
    return {
        "max_interest_rate": 12.0,
        "cooldown_days": 7,
        "currency": "BRL",
    }


def _normalize_cnpj(value: str) -> str:
    """Normaliza e valida um CNPJ."""
    if not value:
        raise ValidationError({"document": "CNPJ e obrigatorio"})

    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise ValidationError({"document": "CNPJ deve conter 14 digitos"})

    if digits == digits[0] * 14:
        raise ValidationError({"document": "CNPJ invalido"})

    def _calc_digit(seq: str, weights: list[int]) -> str:
        total = sum(int(num) * weight for num, weight in zip(seq, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = _calc_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = _calc_digit(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])

    if digits[12] != first_digit or digits[13] != second_digit:
        raise ValidationError({"document": "CNPJ invalido"})

    return digits


_DOMAIN_PATTERN = re.compile(
    r"^(?=.{4,100}$)(?!-)[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)


class BaseTenantModel(models.Model):
    """
    Model base para multi-tenancy com auditoria automatica.

    Todos os models do IABANK devem herdar desta classe para:
    - Garantir isolamento por tenant_id
    - Ter auditoria automatica com django-simple-history
    - Campos padrao (created_at, updated_at)
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
        null=False,
        blank=False,
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

    # Auditoria automatica com django-simple-history
    history = HistoricalRecords(
        inherit=True,
        excluded_fields=["updated_at"],  # updated_at e redundante no historico
        history_id_field=models.UUIDField(default=uuid.uuid4),
        custom_model_name=lambda x: f"Historical{x}",
    )

    class Meta:
        abstract = True
        # Indices compostos obrigatorios com tenant_id primeiro
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
        Override do save com preenchimento automatico e validacao de tenant_id.

        Raises:
            ValueError: Se tenant_id nao for informado ou for alterado indevidamente
        """
        tenant_identifier = self.tenant_id or self._get_tenant_id_from_context()
        if not tenant_identifier:
            raise ValueError("tenant_id e obrigatorio para todos os models")

        self.tenant_id = self._normalize_tenant_id(tenant_identifier)

        if not self._state.adding and self.pk is not None:
            original_tenant_id = (
                self.__class__._default_manager.filter(pk=self.pk)
                .values_list("tenant_id", flat=True)
                .first()
            )
            if original_tenant_id is not None:
                original_uuid = self._normalize_tenant_id(original_tenant_id)
                if original_uuid != self.tenant_id:
                    raise ValueError(
                        "tenant_id nao pode ser alterado apos criacao do registro"
                    )

        super().save(*args, **kwargs)

    def _get_tenant_id_from_context(self) -> uuid.UUID | None:
        """Obtem tenant_id do contexto corrente se disponivel."""
        try:
            from iabank.core.middleware import TenantMiddleware
        except Exception:
            return None

        tenant = TenantMiddleware.get_current_tenant()
        if tenant is None:
            return None

        tenant_id = getattr(tenant, "id", None)
        return self._normalize_tenant_id(tenant_id) if tenant_id else None

    @staticmethod
    def _normalize_tenant_id(value: Any) -> uuid.UUID:
        """Normaliza diferentes formatos de tenant_id para UUID."""
        if isinstance(value, uuid.UUID):
            return value

        if value is None:
            raise ValueError("tenant_id e obrigatorio para todos os models")

        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("tenant_id e obrigatorio para todos os models")
            return uuid.UUID(value)

        if hasattr(value, "hex") and isinstance(value.hex, str):
            return uuid.UUID(value.hex)

        raise ValueError("tenant_id deve ser um UUID valido")

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
        """String representation padrao."""
        return f"{self.__class__.__name__}({self.id})"


class Tenant(BaseTenantModel):
    """Model que representa a empresa cliente da plataforma."""

    name = models.CharField(
        max_length=255,
        help_text="Nome legal da empresa",
    )
    slug = models.SlugField(
        max_length=60,
        unique=True,
        blank=True,
        help_text="Identificador curto usado em subdomínios",
    )
    document = models.CharField(
        max_length=14,
        unique=True,
        help_text="CNPJ da empresa somente com dígitos",
        db_index=True,
    )
    domain = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Domínio customizado do tenant (opcional)",
    )
    contact_email = models.EmailField(
        blank=True,
        help_text="Email principal de contato",
    )
    phone_number = models.CharField(
        max_length=32,
        blank=True,
        help_text="Telefone comercial do tenant",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Tenant ativo na plataforma",
        db_index=True,
    )
    created_by = models.CharField(
        max_length=200,
        help_text="Usuário responsável pela criação",
        blank=True,
    )
    settings = models.JSONField(
        default=_default_tenant_settings,
        help_text="Configurações específicas do tenant",
    )

    class Meta:
        db_table = "core_tenants"
        indexes = [
            models.Index(fields=["document"], name="core_tenants_document_idx"),
            models.Index(fields=["is_active"], name="core_tenants_active_idx"),
        ]

    def clean(self):
        super().clean()

        self.document = _normalize_cnpj(self.document)

        if self.domain:
            normalized_domain = self.domain.strip().lower()
            if not _DOMAIN_PATTERN.match(normalized_domain):
                raise ValidationError({"domain": "Dominio invalido"})
            self.domain = normalized_domain

        slug_field = self._meta.get_field("slug")
        base_slug = slugify(self.slug or self.name)
        if not base_slug:
            raise ValidationError({"slug": "Slug nao pode ser vazio"})

        base_slug = base_slug[: slug_field.max_length]
        self.slug = self._build_unique_slug(base_slug, slug_field.max_length)

    def _build_unique_slug(self, base_slug: str, max_length: int) -> str:
        """Gera slug unico respeitando o tamanho maximo."""
        candidate = base_slug
        suffix = 2
        while self.__class__.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
            suffix_str = f"-{suffix}"
            candidate = f"{base_slug[: max_length - len(suffix_str)]}{suffix_str}"
            suffix += 1
        return candidate

    def save(self, *args, **kwargs):
        """Garante que tenant_id sempre corresponda ao proprio id."""
        if not self.id:
            self.id = uuid.uuid4()
        self.tenant_id = self.id

        self.document = _normalize_cnpj(self.document)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def document_formatted(self) -> str:
        """Retorna o CNPJ formatado."""
        digits = self.document
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    def __str__(self) -> str:
        return f"{self.name} ({self.document_formatted})"


