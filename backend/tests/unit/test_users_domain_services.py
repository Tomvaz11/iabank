"""Testes unitários para camada de domínio de usuários."""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from iabank.users.domain.entities import (
    ConsultantEntity,
    UserEntity,
    UserRole,
    build_login_identifier,
)
from iabank.users.domain.services import (
    ConsultantCommissionInput,
    ConsultantCreateInput,
    ConsultantService,
    DomainError,
    MFAOperationError,
    PasswordPolicyError,
    UserCreateInput,
    UserService,
    UserUpdateInput,
)


def _make_uuid(value: str) -> UUID:
    return UUID(value)


def test_user_entity_generates_login_identifier() -> None:
    tenant_id = _make_uuid("11111111-2222-3333-4444-555555555555")
    entity = UserEntity(
        tenant_id=tenant_id,
        email="user@example.com",
        first_name="Maria",
        last_name="Silva",
        role=UserRole.MANAGER,
    )

    expected_identifier = build_login_identifier(tenant_id, "user@example.com")
    assert entity.login_identifier == expected_identifier
    assert entity.full_name() == "Maria Silva"


def test_user_entity_requires_mfa_secret_when_enabled() -> None:
    tenant_id = uuid4()
    with pytest.raises(ValueError):
        UserEntity(
            tenant_id=tenant_id,
            email="secure@example.com",
            role=UserRole.ADMIN,
            mfa_enabled=True,
        )


def test_consultant_entity_validates_user_role() -> None:
    tenant_id = uuid4()
    user = UserEntity(
        tenant_id=tenant_id,
        email="consultor@example.com",
        role=UserRole.MANAGER,
    )

    with pytest.raises(ValueError):
        ConsultantEntity(
            tenant_id=tenant_id,
            user_id=uuid4(),
            user=user,
            commission_rate=Decimal("0.10"),
        )


def test_user_service_password_policy_enforced() -> None:
    payload = UserCreateInput(
        tenant_id=uuid4(),
        email="weak@example.com",
        password="weakpass",
    )
    with pytest.raises(PasswordPolicyError):
        UserService.create_user(payload)


def test_user_service_update_user_rebuilds_login_identifier() -> None:
    tenant_id = uuid4()
    entity = UserEntity(
        tenant_id=tenant_id,
        email="old@example.com",
        role=UserRole.MANAGER,
    )
    update = UserUpdateInput(email="new@example.com")

    updated = UserService.update_user(entity, update)

    assert updated.email == "new@example.com"
    assert updated.login_identifier == build_login_identifier(tenant_id, "new@example.com")


def test_user_service_prevents_disabling_mfa_after_enabled() -> None:
    tenant_id = uuid4()
    entity = UserEntity(
        tenant_id=tenant_id,
        email="mfa@example.com",
        role=UserRole.ADMIN,
        mfa_enabled=True,
        mfa_secret="secret123",
    )
    update = UserUpdateInput(mfa_enabled=False)

    with pytest.raises(MFAOperationError):
        UserService.update_user(entity, update)


def test_consultant_service_adjust_commission_balance() -> None:
    tenant_id = uuid4()
    user = UserEntity(
        tenant_id=tenant_id,
        email="consultor@example.com",
        role=UserRole.CONSULTANT,
        id=uuid4(),
    )
    input_data = ConsultantCreateInput(
        tenant_id=tenant_id,
        user_id=user.id,
        commission_rate=Decimal("0.05"),
    )
    consultant = ConsultantService.create_consultant(user, input_data)

    adjustment = ConsultantCommissionInput(amount=Decimal("150.55"))
    updated = ConsultantService.adjust_commission_balance(consultant, adjustment)

    assert updated.commission_balance == Decimal("150.55")


def test_consultant_service_set_commission_rate_validates_bounds() -> None:
    tenant_id = uuid4()
    user = UserEntity(
        tenant_id=tenant_id,
        email="consultor@example.com",
        role=UserRole.CONSULTANT,
        id=uuid4(),
    )
    consultant = ConsultantService.create_consultant(
        user,
        ConsultantCreateInput(tenant_id=tenant_id, user_id=user.id, commission_rate=Decimal("0.10")),
    )

    updated = ConsultantService.set_commission_rate(consultant, Decimal("0.25"))
    assert updated.commission_rate == Decimal("0.2500")

    with pytest.raises(DomainError):
        ConsultantService.set_commission_rate(consultant, Decimal("1.5"))
