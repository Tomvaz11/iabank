"""Entidades de domínio para o módulo de usuários."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRole(StrEnum):
    """Papéis suportados pelo RBAC do sistema."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CONSULTANT = "CONSULTANT"
    COLLECTOR = "COLLECTOR"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    FINANCE_ANALYST = "FINANCE_ANALYST"
    COMPLIANCE_MANAGER = "COMPLIANCE_MANAGER"


def build_login_identifier(tenant_id: UUID, email: str) -> str:
    """Combina tenant e email normalizado para gerar identificador único."""

    email_normalized = email.strip().lower()
    if not email_normalized:
        raise ValueError("email é obrigatório para gerar login_identifier")
    return f"{UUID(str(tenant_id))}:{email_normalized}"


class UserEntity(BaseModel):
    """Representa o estado de negócio de um usuário multi-tenant."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None, description="Identificador do usuário")
    tenant_id: UUID = Field(description="Identificador do tenant")
    email: str = Field(description="Email corporativo")
    login_identifier: Optional[str] = Field(
        default=None,
        description="Identificador único composto por tenant e email",
    )
    username: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Alias curto opcional",
    )
    first_name: Optional[str] = Field(default=None, max_length=150)
    last_name: Optional[str] = Field(default=None, max_length=150)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    role: UserRole = Field(default=UserRole.MANAGER)
    is_active: bool = Field(default=True)
    is_staff: bool = Field(default=False)
    is_superuser: bool = Field(default=False)
    date_joined: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(default=None)
    mfa_enabled: bool = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None, max_length=128)
    tenant_locked: bool = Field(
        default=False,
        description="Indica se tenant_id pode ser alterado",
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Email inválido")
        return normalized

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if len(value) > 150:
            raise ValueError("username deve ter no máximo 150 caracteres")
        return value

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def _normalize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("mfa_secret")
    @classmethod
    def _trim_secret(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _validate_consistency(self) -> "UserEntity":
        if self.mfa_enabled and not self.mfa_secret:
            raise ValueError("Segredo MFA é obrigatório quando MFA estiver habilitado.")

        if not self.mfa_enabled:
            object.__setattr__(self, "mfa_secret", None)

        object.__setattr__(self, "login_identifier", build_login_identifier(self.tenant_id, str(self.email)))
        return self

    def full_name(self) -> str:
        """Retorna representação amigável do nome completo."""

        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        combined = f"{first} {last}".strip()
        return combined or self.username or str(self.email)

    def short_name(self) -> str:
        """Retorna nome curto para exibição."""

        if self.first_name:
            return self.first_name
        if self.username:
            return self.username
        return str(self.email)

    @property
    def can_change_tenant(self) -> bool:
        """Indica se tenant pode ser alterado segundo regras de bloqueio."""

        return not self.tenant_locked


class ConsultantEntity(BaseModel):
    """Representa o estado de negócio de um consultor."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID = Field(description="Tenant associado")
    user_id: UUID = Field(description="Usuário vinculado")
    user: Optional[UserEntity] = Field(default=None, description="Usuário completo opcional")
    commission_rate: Decimal = Field(
        default=Decimal("0"),
        description="Percentual de comissão do consultor",
    )
    commission_balance: Decimal = Field(
        default=Decimal("0"),
        description="Saldo atual de comissões",
    )
    bank_account: Optional[str] = Field(default=None, max_length=50)
    is_active_for_loans: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("commission_rate", mode="before")
    @classmethod
    def _coerce_rate(cls, value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    @field_validator("commission_rate")
    @classmethod
    def _validate_rate(cls, value: Decimal) -> Decimal:
        if value < Decimal("0") or value > Decimal("1"):
            raise ValueError("commission_rate deve estar entre 0 e 1")
        return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @field_validator("commission_balance", mode="before")
    @classmethod
    def _coerce_balance(cls, value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    @field_validator("commission_balance")
    @classmethod
    def _quantize_balance(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @model_validator(mode="after")
    def _validate_user_context(self) -> "ConsultantEntity":
        if self.user is not None:
            if self.user.id is not None and self.user.id != self.user_id:
                raise ValueError("user_id deve coincidir com o usuário associado")
            if self.user.tenant_id != self.tenant_id:
                raise ValueError("Consultor e usuário associados devem pertencer ao mesmo tenant")
            if self.user.role is not UserRole.CONSULTANT:
                raise ValueError("Usuário associado deve possuir papel CONSULTANT")
        return self

    def can_receive_commission(self) -> bool:
        """Indica se consultor pode originar novos empréstimos."""

        return self.is_active_for_loans
