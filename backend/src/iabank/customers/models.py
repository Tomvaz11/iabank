"""Modelos relacionados a clientes (Customer)."""
from __future__ import annotations

import hashlib
import re
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from iabank.core.fields import EncryptedCharField, EncryptedEmailField
from iabank.core.models import BaseTenantModel, _normalize_cnpj


_CPF_INVALID_SEQUENCES = {"0" * 11, "1" * 11, "2" * 11, "3" * 11, "4" * 11, "5" * 11, "6" * 11, "7" * 11, "8" * 11, "9" * 11}


class CustomerDocumentType(models.TextChoices):
    """Tipos de documentos aceitos para clientes."""

    CPF = "CPF", "CPF"
    CNPJ = "CNPJ", "CNPJ"


class CustomerGender(models.TextChoices):
    """Enum com opções de gênero suportadas."""

    MALE = "M", "Masculino"
    FEMALE = "F", "Feminino"
    OTHER = "OTHER", "Outro"


class Customer(BaseTenantModel):
    """Modelo que representa o cliente final (tomador de empréstimo)."""

    document_type = models.CharField(
        max_length=5,
        choices=CustomerDocumentType.choices,
        help_text="Tipo de documento utilizado pelo cliente",
    )
    document = EncryptedCharField(
        max_length=32,
        help_text="Documento do cliente armazenado de forma criptografada",
    )
    document_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text="Hash do documento para garantir unicidade por tenant",
    )
    name = EncryptedCharField(
        max_length=255,
        help_text="Nome completo ou razão social do cliente",
    )
    email = EncryptedEmailField(
        help_text="Email de contato do cliente",
    )
    phone = EncryptedCharField(
        max_length=32,
        blank=True,
        help_text="Telefone principal do cliente",
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        help_text="Data de nascimento (para pessoas físicas)",
    )
    gender = models.CharField(
        max_length=10,
        choices=CustomerGender.choices,
        blank=True,
        help_text="Gênero informado pelo cliente",
    )
    profession = EncryptedCharField(
        max_length=100,
        blank=True,
        help_text="Profissão ou cargo principal",
    )
    monthly_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Renda mensal declarada pelo cliente",
    )
    credit_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
        help_text="Score de crédito (0-1000)",
    )
    score_last_updated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Data/hora da última atualização do score",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se o cliente está ativo para operações",
        db_index=True,
    )

    class Meta:
        db_table = "customers_customers"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "document_hash"],
                name="cust_cust_doc_hash_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["tenant_id", "is_active"],
                name="cust_cust_active_idx",
            ),
            models.Index(
                fields=["tenant_id", "score_last_updated"],
                name="cust_cust_score_idx",
            ),
        ]

    def clean(self):
        super().clean()

        tenant_uuid = self._resolve_tenant_uuid()
        normalized_document = self._normalize_document(self.document_type, self.document)
        self.document = normalized_document
        self.document_hash = self._build_document_hash(tenant_uuid, normalized_document)

        if self.email:
            self.email = self.email.strip().lower()

        if self.name:
            self.name = self.name.strip()

        if self.monthly_income is not None and self.monthly_income <= Decimal("0"):
            raise ValidationError({"monthly_income": "Renda mensal deve ser positiva"})

    def save(self, *args, **kwargs):
        tenant_identifier = self.tenant_id or self._get_tenant_id_from_context()
        if not tenant_identifier:
            raise ValueError("tenant_id é obrigatório para clientes")
        self.tenant_id = self._normalize_tenant_id(tenant_identifier)

        self.full_clean()
        super().save(*args, **kwargs)

    def _resolve_tenant_uuid(self) -> uuid.UUID:
        tenant_identifier = self.tenant_id or self._get_tenant_id_from_context()
        if not tenant_identifier:
            raise ValidationError({"tenant_id": "tenant_id é obrigatório"})
        try:
            return self._normalize_tenant_id(tenant_identifier)
        except ValueError as exc:
            raise ValidationError({"tenant_id": str(exc)}) from exc

    @staticmethod
    def _normalize_document(document_type: str | None, value: str | None) -> str:
        if not document_type:
            raise ValidationError({"document_type": "Tipo de documento é obrigatório"})
        if not value:
            raise ValidationError({"document": "Documento é obrigatório"})

        document_type = document_type.upper()
        if document_type == CustomerDocumentType.CPF:
            return _normalize_cpf(value)
        if document_type == CustomerDocumentType.CNPJ:
            return _normalize_cnpj(value)
        raise ValidationError({"document_type": "Tipo de documento inválido"})

    @staticmethod
    def _build_document_hash(tenant_id: uuid.UUID, normalized_document: str) -> str:
        to_hash = f"{tenant_id}:{normalized_document}".encode("utf-8")
        return hashlib.sha256(to_hash).hexdigest()

    @property
    def document_formatted(self) -> str:
        """Retorna documento formatado conforme o tipo."""
        if not self.document:
            return ""
        digits = re.sub(r"\D", "", self.document)
        if self.document_type == CustomerDocumentType.CPF and len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        if self.document_type == CustomerDocumentType.CNPJ and len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        return digits

    def __str__(self) -> str:
        return f"Customer({self.name})"


def _normalize_cpf(value: str) -> str:
    """Normaliza e valida um CPF."""
    digits = re.sub(r"\D", "", value or "")

    if len(digits) != 11:
        raise ValidationError({"document": "CPF deve conter 11 dígitos"})

    if digits in _CPF_INVALID_SEQUENCES:
        raise ValidationError({"document": "CPF inválido"})

    for i in range(9, 11):
        total = sum(int(digits[num]) * ((i + 1) - num) for num in range(0, i))
        check_digit = ((total * 10) % 11) % 10
        if check_digit != int(digits[i]):
            raise ValidationError({"document": "CPF inválido"})

    return digits
