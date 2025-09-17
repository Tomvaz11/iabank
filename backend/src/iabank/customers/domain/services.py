"""Serviços de domínio para clientes."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .entities import (
    AddressEntity,
    AddressType,
    CustomerDocumentType,
    CustomerEntity,
    CustomerGender,
    InvalidDocumentError,
    build_document_hash,
)


class CustomerDomainError(RuntimeError):
    """Erro genérico da camada de domínio de clientes."""


class DuplicatePrimaryAddressError(CustomerDomainError):
    """Indica múltiplos endereços marcados como primários."""


class AddressCreateInput(BaseModel):
    """Dados necessários para criação de um endereço."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    type: AddressType = Field(default=AddressType.RESIDENTIAL)
    street: str = Field(min_length=1, max_length=255)
    number: str = Field(min_length=1, max_length=20)
    complement: Optional[str] = Field(default=None, max_length=100)
    neighborhood: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2)
    zipcode: str = Field(min_length=8, max_length=9)
    is_primary: bool = Field(default=False)


class AddressUpdateInput(AddressCreateInput):
    """Campos permitidos para atualizar um endereço existente."""

    id: Optional[UUID] = None


class CustomerCreateInput(BaseModel):
    """Dados obrigatórios para criação de cliente."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    document_type: CustomerDocumentType
    document: str
    name: str
    email: str
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[CustomerGender] = None
    profession: Optional[str] = None
    monthly_income: Optional[Decimal] = None
    credit_score: Optional[int] = None
    addresses: List[AddressCreateInput] = Field(default_factory=list)

    @field_validator("document")
    @classmethod
    def _strip_document(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def _strip_email(cls, value: str) -> str:
        return value.strip()


class CustomerUpdateInput(BaseModel):
    """Campos opcionais para atualização de cliente."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_type: Optional[CustomerDocumentType] = None
    document: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[CustomerGender] = None
    profession: Optional[str] = None
    monthly_income: Optional[Decimal] = None
    credit_score: Optional[int] = None

    @field_validator("document", mode="before")
    @classmethod
    def _strip_document(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()

    @field_validator("email")
    @classmethod
    def _strip_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()


class CustomerService:
    """Serviços para gerenciamento da entidade de cliente."""

    @classmethod
    def create_customer(cls, data: CustomerCreateInput) -> CustomerEntity:
        addresses = cls._build_addresses(
            tenant_id=data.tenant_id,
            customer_id=None,
            addresses=data.addresses,
        )
        return CustomerEntity(
            tenant_id=data.tenant_id,
            document_type=data.document_type,
            document=data.document,
            name=data.name,
            email=data.email,
            phone=data.phone,
            birth_date=data.birth_date,
            gender=data.gender,
            profession=data.profession,
            monthly_income=data.monthly_income,
            credit_score=data.credit_score,
            addresses=addresses,
        )

    @classmethod
    def update_customer(cls, customer: CustomerEntity, data: CustomerUpdateInput) -> CustomerEntity:
        updates: dict[str, object] = {}

        if data.document is not None or data.document_type is not None:
            document_type = data.document_type or customer.document_type
            if data.document is None:
                raise InvalidDocumentError("Documento é obrigatório ao alterar o tipo")
            normalized_document = CustomerEntity._normalize_document(document_type, data.document)
            updates["document_type"] = document_type
            updates["document"] = normalized_document
            updates["document_hash"] = build_document_hash(customer.tenant_id, normalized_document)

        for field_name in ("name", "email", "phone", "birth_date", "gender", "profession"):
            value = getattr(data, field_name)
            if value is not None:
                updates[field_name] = value

        if data.monthly_income is not None:
            updates["monthly_income"] = data.monthly_income

        if data.credit_score is not None:
            updates["credit_score"] = data.credit_score
            updates["score_last_updated"] = datetime.now(timezone.utc)

        if not updates:
            return customer

        return customer.model_copy(update=updates)

    @classmethod
    def update_credit_score(
        cls,
        customer: CustomerEntity,
        *,
        credit_score: int,
        as_of: Optional[datetime] = None,
    ) -> CustomerEntity:
        timestamp = as_of or datetime.now(timezone.utc)
        return customer.model_copy(update={"credit_score": credit_score, "score_last_updated": timestamp})

    @classmethod
    def activate(cls, customer: CustomerEntity) -> CustomerEntity:
        if customer.is_active:
            return customer
        return customer.model_copy(update={"is_active": True})

    @classmethod
    def deactivate(cls, customer: CustomerEntity) -> CustomerEntity:
        if not customer.is_active:
            return customer
        return customer.model_copy(update={"is_active": False})

    @classmethod
    def add_address(
        cls,
        customer: CustomerEntity,
        address_input: AddressCreateInput,
    ) -> CustomerEntity:
        addresses = list(customer.addresses)
        candidate = cls._build_addresses(
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            addresses=[address_input],
        )[0]

        if candidate.is_primary:
            for idx, address in enumerate(addresses):
                if address.is_primary:
                    addresses[idx] = address.model_copy(update={"is_primary": False})

        addresses.append(candidate)
        return customer.with_addresses(addresses)

    @classmethod
    def replace_addresses(
        cls,
        customer: CustomerEntity,
        addresses: Iterable[AddressCreateInput | AddressUpdateInput],
    ) -> CustomerEntity:
        address_list = list(addresses)
        built = cls._build_addresses(
            tenant_id=customer.tenant_id,
            customer_id=customer.id,
            addresses=address_list,
        )
        return customer.with_addresses(built)

    @classmethod
    def _build_addresses(
        cls,
        *,
        tenant_id: UUID,
        customer_id: Optional[UUID],
        addresses: Iterable[AddressCreateInput | AddressUpdateInput],
    ) -> List[AddressEntity]:
        address_list = list(addresses or [])
        if not address_list:
            return []

        primary_count = sum(1 for item in address_list if item.is_primary)
        if primary_count > 1:
            raise DuplicatePrimaryAddressError("Somente um endereço pode ser principal")

        set_primary_index: Optional[int] = None
        if primary_count == 0:
            set_primary_index = 0

        built: List[AddressEntity] = []
        for index, address in enumerate(address_list):
            is_primary = address.is_primary or (set_primary_index is not None and index == set_primary_index)
            built.append(
                AddressEntity(
                    id=getattr(address, "id", None),
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    type=address.type,
                    street=address.street,
                    number=address.number,
                    complement=address.complement,
                    neighborhood=address.neighborhood,
                    city=address.city,
                    state=address.state,
                    zipcode=address.zipcode,
                    is_primary=is_primary,
                )
            )

        return built


__all__ = [
    "AddressCreateInput",
    "AddressUpdateInput",
    "CustomerCreateInput",
    "CustomerUpdateInput",
    "CustomerService",
    "CustomerDomainError",
    "DuplicatePrimaryAddressError",
    "InvalidDocumentError",
]

