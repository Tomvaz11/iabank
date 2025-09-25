"""Entidades de domínio para clientes e endereços."""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from hashlib import sha256
from typing import Iterable, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CPF_INVALID_SEQUENCES = {str(num) * 11 for num in range(10)}


class InvalidDocumentError(RuntimeError):
    """Representa falhas de validação de documento (CPF/CNPJ)."""


class CustomerDocumentType(StrEnum):
    """Tipos de documentos aceitos para clientes."""

    CPF = "CPF"
    CNPJ = "CNPJ"


class CustomerGender(StrEnum):
    """Opções de gênero suportadas no cadastro."""

    MALE = "M"
    FEMALE = "F"
    OTHER = "OTHER"


class AddressType(StrEnum):
    """Tipos de endereço suportados."""

    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    CORRESPONDENCE = "CORRESPONDENCE"


class AddressState(StrEnum):
    """Unidades federativas brasileiras."""

    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"


def _normalize_cpf(value: str | None) -> str:
    if not value:
        raise InvalidDocumentError("CPF é obrigatório")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        raise InvalidDocumentError("CPF deve conter 11 dígitos")

    if digits in CPF_INVALID_SEQUENCES:
        raise InvalidDocumentError("CPF inválido")

    for i in range(9, 11):
        total = sum(int(digits[num]) * ((i + 1) - num) for num in range(0, i))
        check_digit = ((total * 10) % 11) % 10
        if check_digit != int(digits[i]):
            raise InvalidDocumentError("CPF inválido")

    return digits


def _normalize_cnpj(value: str | None) -> str:
    if not value:
        raise InvalidDocumentError("CNPJ é obrigatório")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise InvalidDocumentError("CNPJ deve conter 14 dígitos")

    if digits == digits[0] * 14:
        raise InvalidDocumentError("CNPJ inválido")

    def _calc_digit(seq: str, weights: List[int]) -> str:
        total = sum(int(num) * weight for num, weight in zip(seq, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = _calc_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = _calc_digit(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])

    if digits[12] != first_digit or digits[13] != second_digit:
        raise InvalidDocumentError("CNPJ inválido")

    return digits


def build_document_hash(tenant_id: UUID, normalized_document: str) -> str:
    """Gera hash determinístico para documento dentro do tenant."""

    return sha256(f"{tenant_id}:{normalized_document}".encode("utf-8")).hexdigest()


class AddressEntity(BaseModel):
    """Representa endereço associado a um cliente."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant proprietário do endereço")
    customer_id: Optional[UUID] = Field(default=None, description="Cliente ao qual pertence")
    type: AddressType = Field(default=AddressType.RESIDENTIAL)
    street: str = Field(min_length=1, max_length=255)
    number: str = Field(min_length=1, max_length=20)
    complement: Optional[str] = Field(default=None, max_length=100)
    neighborhood: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zipcode: str = Field(min_length=8, max_length=9)
    is_primary: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("street", "number", "neighborhood", "city", "complement", mode="before")
    @classmethod
    def _normalize_strings(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("state")
    @classmethod
    def _normalize_state(cls, value: str) -> str:
        state = value.strip().upper()
        if state not in AddressState._value2member_map_:
            raise ValueError("UF inválida")
        return state

    @field_validator("zipcode")
    @classmethod
    def _normalize_zipcode(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value or "")
        if len(digits) != 8:
            raise ValueError("CEP deve conter 8 dígitos")
        return f"{digits[:5]}-{digits[5:]}"


class CustomerEntity(BaseModel):
    """Entidade de negócio para cliente multi-tenant."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant proprietário do cliente")
    document_type: CustomerDocumentType = Field(description="Tipo de documento")
    document: str = Field(min_length=5, max_length=32)
    document_hash: Optional[str] = Field(default=None)
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=32)
    birth_date: Optional[date] = Field(default=None)
    gender: Optional[CustomerGender] = Field(default=None)
    profession: Optional[str] = Field(default=None, max_length=100)
    monthly_income: Optional[Decimal] = Field(default=None)
    credit_score: Optional[int] = Field(default=None)
    score_last_updated: Optional[datetime] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    addresses: List[AddressEntity] = Field(default_factory=list)

    @field_validator("gender", mode="before")
    @classmethod
    def _normalize_gender(cls, value: Optional[str | CustomerGender]) -> Optional[CustomerGender | str]:
        if value is None:
            return None
        if isinstance(value, CustomerGender):
            return value
        normalized = str(value).strip()
        if not normalized:
            return None
        return CustomerGender(normalized.upper())

    @field_validator("addresses", mode="before")
    @classmethod
    def _normalize_addresses(cls, value: Optional[Iterable]) -> List[AddressEntity] | Iterable:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if hasattr(value, "all"):
            return list(value.all())
        if isinstance(value, tuple):
            return list(value)
        return value

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_REGEX.match(email):
            raise ValueError("Email inválido")
        return email

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("profession")
    @classmethod
    def _normalize_profession(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("monthly_income", mode="before")
    @classmethod
    def _coerce_income(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return None
        return Decimal(str(value))

    @field_validator("monthly_income")
    @classmethod
    def _validate_income(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return None
        if value <= Decimal("0"):
            raise ValueError("monthly_income deve ser positivo")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @field_validator("credit_score")
    @classmethod
    def _validate_credit_score(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 0 or value > 1000:
            raise ValueError("credit_score deve estar entre 0 e 1000")
        return int(value)

    @model_validator(mode="after")
    def _apply_document_rules(self) -> "CustomerEntity":
        normalized = self._normalize_document(self.document_type, self.document)
        object.__setattr__(self, "document", normalized)

        if self.document_hash is None:
            object.__setattr__(self, "document_hash", build_document_hash(self.tenant_id, normalized))

        if self.birth_date is not None and self.birth_date > date.today():
            raise ValueError("birth_date não pode ser futura")

        return self

    @staticmethod
    def _normalize_document(document_type: CustomerDocumentType, value: str) -> str:
        if document_type == CustomerDocumentType.CPF:
            return _normalize_cpf(value)
        if document_type == CustomerDocumentType.CNPJ:
            return _normalize_cnpj(value)
        raise InvalidDocumentError("Tipo de documento inválido")

    def with_addresses(self, addresses: List[AddressEntity]) -> "CustomerEntity":
        """Retorna nova entidade com endereços substituídos."""

        return self.model_copy(update={"addresses": addresses})
