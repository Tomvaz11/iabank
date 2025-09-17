"""Testes unitários para a camada de domínio de clientes."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from iabank.customers.domain.entities import (
    AddressEntity,
    AddressType,
    CustomerDocumentType,
    CustomerEntity,
)
from iabank.customers.domain.services import (
    AddressCreateInput,
    CustomerCreateInput,
    CustomerService,
    DuplicatePrimaryAddressError,
    InvalidDocumentError,
)


def _expected_hash(tenant_id: UUID, document: str) -> str:
    from hashlib import sha256

    return sha256(f"{tenant_id}:{document}".encode("utf-8")).hexdigest()


def test_customer_entity_normalizes_document_and_computes_hash() -> None:
    tenant_id = uuid4()
    entity = CustomerEntity(
        tenant_id=tenant_id,
        document_type=CustomerDocumentType.CPF,
        document="529.982.247-25",
        name=" Joao Silva ",
        email="JOAO.SILVA@EXEMPLO.COM",
        phone=" (11) 99999-0000 ",
        monthly_income=Decimal("5500.00"),
    )

    assert entity.document == "52998224725"
    assert entity.document_hash == _expected_hash(tenant_id, "52998224725")
    assert entity.email == "joao.silva@exemplo.com"
    assert entity.name == "Joao Silva"
    assert entity.is_active is True


def test_customer_entity_rejects_invalid_document() -> None:
    tenant_id = uuid4()
    with pytest.raises(InvalidDocumentError):
        CustomerEntity(
            tenant_id=tenant_id,
            document_type=CustomerDocumentType.CPF,
            document="123.456.789-00",
            name="Cliente Teste",
            email="cliente@example.com",
        )


def test_customer_entity_rejects_invalid_monthly_income() -> None:
    tenant_id = uuid4()
    with pytest.raises(ValueError):
        CustomerEntity(
            tenant_id=tenant_id,
            document_type=CustomerDocumentType.CPF,
            document="529.982.247-25",
            name="Cliente Teste",
            email="cliente@example.com",
            monthly_income=Decimal("-1"),
        )


def test_address_entity_normalizes_state_and_zipcode() -> None:
    tenant_id = uuid4()
    customer_id = uuid4()

    address = AddressEntity(
        tenant_id=tenant_id,
        customer_id=customer_id,
        type=AddressType.RESIDENTIAL,
        street=" Rua das Flores ",
        number=" 123 ",
        neighborhood=" Centro ",
        city=" Sao Paulo ",
        state="sp",
        zipcode="01001-000",
        is_primary=True,
    )

    assert address.state == "SP"
    assert address.zipcode == "01001-000"
    assert address.street == "Rua das Flores"
    assert address.number == "123"
    assert address.neighborhood == "Centro"
    assert address.city == "Sao Paulo"


def test_customer_service_create_customer_generates_primary_address() -> None:
    tenant_id = uuid4()
    payload = CustomerCreateInput(
        tenant_id=tenant_id,
        document_type=CustomerDocumentType.CPF,
        document="529.982.247-25",
        name="Joao Silva",
        email="joao@example.com",
        monthly_income=Decimal("7500.00"),
        addresses=[
            AddressCreateInput(
                type=AddressType.RESIDENTIAL,
                street="Rua A",
                number="123",
                neighborhood="Centro",
                city="Sao Paulo",
                state="SP",
                zipcode="01001000",
            ),
            AddressCreateInput(
                type=AddressType.COMMERCIAL,
                street="Rua B",
                number="456",
                neighborhood="Bairro",
                city="Sao Paulo",
                state="SP",
                zipcode="02002000",
                is_primary=True,
            ),
        ],
    )

    customer = CustomerService.create_customer(payload)

    assert customer.document_hash == _expected_hash(tenant_id, "52998224725")
    assert len(customer.addresses) == 2
    assert customer.addresses[1].is_primary is True
    assert customer.addresses[1].zipcode == "02002-000"
    assert all(address.tenant_id == tenant_id for address in customer.addresses)


def test_customer_service_raises_error_for_duplicate_primary_addresses() -> None:
    tenant_id = uuid4()
    payload = CustomerCreateInput(
        tenant_id=tenant_id,
        document_type=CustomerDocumentType.CPF,
        document="529.982.247-25",
        name="Joao Silva",
        email="joao@example.com",
        addresses=[
            AddressCreateInput(
                type=AddressType.RESIDENTIAL,
                street="Rua A",
                number="123",
                neighborhood="Centro",
                city="Sao Paulo",
                state="SP",
                zipcode="01001000",
                is_primary=True,
            ),
            AddressCreateInput(
                type=AddressType.COMMERCIAL,
                street="Rua B",
                number="456",
                neighborhood="Bairro",
                city="Sao Paulo",
                state="SP",
                zipcode="02002000",
                is_primary=True,
            ),
        ],
    )

    with pytest.raises(DuplicatePrimaryAddressError):
        CustomerService.create_customer(payload)


def test_customer_service_update_credit_score_sets_timestamp() -> None:
    tenant_id = uuid4()
    customer = CustomerEntity(
        id=uuid4(),
        tenant_id=tenant_id,
        document_type=CustomerDocumentType.CPF,
        document="529.982.247-25",
        name="Cliente",
        email="cliente@example.com",
    )

    updated = CustomerService.update_credit_score(customer, credit_score=720)

    assert updated.credit_score == 720
    assert updated.score_last_updated is not None
    assert updated.score_last_updated > datetime.now(timezone.utc) - timedelta(seconds=5)


def test_customer_service_toggle_active_state() -> None:
    tenant_id = uuid4()
    customer = CustomerEntity(
        tenant_id=tenant_id,
        document_type=CustomerDocumentType.CPF,
        document="529.982.247-25",
        name="Cliente",
        email="cliente@example.com",
    )

    inactive = CustomerService.deactivate(customer)
    assert inactive.is_active is False

    active_again = CustomerService.activate(inactive)
    assert active_again.is_active is True

