"""Serviços de domínio para regras de negócio de usuários e consultores."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .entities import (
    ConsultantEntity,
    EMAIL_REGEX,
    UserEntity,
    UserRole,
    build_login_identifier,
)


class DomainError(RuntimeError):
    """Erro genérico da camada de domínio."""


class PasswordPolicyError(DomainError):
    """Violação da política de senhas."""


class TenantLockError(DomainError):
    """Tentativa de alterar tenant em usuário bloqueado."""


class InvalidRoleError(DomainError):
    """Uso de papel incompatível com a operação."""


class MFAOperationError(DomainError):
    """Operações inválidas envolvendo MFA."""


class UserCreateInput(BaseModel):
    """Dados obrigatórios para criação de um usuário."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    email: str
    password: str = Field(min_length=8, description="Senha em texto plano (será hasheada na infraestrutura)")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = Field(default=None, max_length=150)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    role: UserRole = UserRole.MANAGER
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = Field(default=None, max_length=128)
    tenant_locked: bool = False
    date_joined: Optional[datetime] = None

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Email inválido")
        return normalized


    @field_validator("password")
    @classmethod
    def _strip_password(cls, value: str) -> str:
        return value.strip()

    @field_validator("mfa_secret")
    @classmethod
    def _strip_secret(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _validate_mfa(self) -> "UserCreateInput":
        if self.mfa_enabled and not self.mfa_secret:
            raise MFAOperationError("Segredo MFA é obrigatório ao habilitar MFA.")
        return self


class UserUpdateInput(BaseModel):
    """Campos permitidos para atualização de um usuário."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = Field(default=None, max_length=150)
    phone_number: Optional[str] = Field(default=None, max_length=32)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_staff: Optional[bool] = None
    is_superuser: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    mfa_secret: Optional[str] = Field(default=None, max_length=128)

    @field_validator("email")
    @classmethod
    def _validate_update_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not EMAIL_REGEX.match(normalized):
            raise ValueError("Email inválido")
        return normalized

    @field_validator("mfa_secret")
    @classmethod
    def _strip_secret(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _validate_mfa(self) -> "UserUpdateInput":
        if self.mfa_enabled is True and not self.mfa_secret:
            raise MFAOperationError("Segredo MFA é obrigatório ao habilitar MFA.")
        return self


class ConsultantCreateInput(BaseModel):
    """Dados necessários para criação de um consultor."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    user_id: UUID
    commission_rate: Decimal = Field(default=Decimal("0"))
    bank_account: Optional[str] = Field(default=None, max_length=50)
    is_active_for_loans: bool = True

    @field_validator("commission_rate", mode="before")
    @classmethod
    def _coerce_rate(cls, value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))


class ConsultantCommissionInput(BaseModel):
    """Dados para ajustar saldo de comissão."""

    model_config = ConfigDict(validate_assignment=True)

    amount: Decimal

    @field_validator("amount", mode="before")
    @classmethod
    def _coerce_amount(cls, value) -> Decimal:
        return Decimal(str(value))


class UserService:
    """Serviços de domínio para usuários."""

    PASSWORD_MIN_LENGTH = 12
    SPECIAL_CHARACTERS = tuple("!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~")

    @classmethod
    def validate_password_strength(cls, password: str) -> None:
        """Garante que senha atende aos requisitos mínimos de segurança."""

        if password is None:
            raise PasswordPolicyError("Senha não pode ser vazia.")

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            raise PasswordPolicyError(
                f"Senha deve ter pelo menos {cls.PASSWORD_MIN_LENGTH} caracteres."
            )

        has_lower = any(ch.islower() for ch in password)
        has_upper = any(ch.isupper() for ch in password)
        has_digit = any(ch.isdigit() for ch in password)
        has_special = any(ch in cls.SPECIAL_CHARACTERS for ch in password)

        if not all([has_lower, has_upper, has_digit, has_special]):
            raise PasswordPolicyError(
                "Senha deve conter letras maiúsculas, minúsculas, números e caracteres especiais."
            )

        if password.lower() in {"password", "123456", "abc123", "iabank"}:
            raise PasswordPolicyError("Senha muito fraca ou comum.")

    @classmethod
    def create_user(cls, data: UserCreateInput) -> UserEntity:
        """Cria entidade de usuário aplicando política de senha e normalizações."""

        cls.validate_password_strength(data.password)
        effective_date_joined = data.date_joined or datetime.now(timezone.utc)

        return UserEntity(
            tenant_id=data.tenant_id,
            email=data.email,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            role=data.role,
            is_active=data.is_active,
            is_staff=data.is_staff,
            is_superuser=data.is_superuser,
            date_joined=effective_date_joined,
            mfa_enabled=data.mfa_enabled,
            mfa_secret=data.mfa_secret,
            tenant_locked=data.tenant_locked,
        )

    @classmethod
    def update_user(cls, user: UserEntity, data: UserUpdateInput) -> UserEntity:
        """Atualiza campos permitidos, preservando regras de negócio."""

        updates: dict[str, object] = {}

        if data.email is not None and data.email != user.email:
            updates["email"] = data.email
            updates["login_identifier"] = build_login_identifier(user.tenant_id, str(data.email))

        for field_name in ("first_name", "last_name", "username", "phone_number"):
            value = getattr(data, field_name)
            if value is not None:
                updates[field_name] = value

        for flag in ("is_active", "is_staff", "is_superuser"):
            value = getattr(data, flag)
            if value is not None:
                updates[flag] = value

        if data.role is not None:
            updates["role"] = data.role

        if data.mfa_enabled is not None:
            if user.mfa_enabled and data.mfa_enabled is False:
                raise MFAOperationError("MFA não pode ser desabilitado após habilitação.")
            if data.mfa_enabled and not data.mfa_secret:
                raise MFAOperationError("Segredo MFA é obrigatório ao habilitar MFA.")
            updates["mfa_enabled"] = data.mfa_enabled
            updates["mfa_secret"] = data.mfa_secret
        elif data.mfa_secret is not None:
            if not user.mfa_enabled:
                raise MFAOperationError("Não é possível alterar segredo MFA sem habilitar MFA.")
            updates["mfa_secret"] = data.mfa_secret

        if not updates:
            return user

        return user.model_copy(update=updates)

    @classmethod
    def activate(cls, user: UserEntity) -> UserEntity:
        """Ativa usuário caso esteja inativo."""

        if user.is_active:
            return user
        return user.model_copy(update={"is_active": True})

    @classmethod
    def deactivate(cls, user: UserEntity) -> UserEntity:
        """Desativa usuários comuns, preservando regras administrativas."""

        if user.is_superuser:
            raise InvalidRoleError("Superusuários não podem ser desativados pela camada de domínio.")
        if not user.is_active:
            return user
        return user.model_copy(update={"is_active": False})

    @classmethod
    def change_role(cls, user: UserEntity, new_role: UserRole) -> UserEntity:
        """Altera papel do usuário."""

        if user.role == new_role:
            return user
        return user.model_copy(update={"role": new_role})

    @classmethod
    def change_tenant(cls, user: UserEntity, new_tenant_id: UUID) -> UserEntity:
        """Move usuário para outro tenant respeitando bloqueios."""

        if not user.can_change_tenant:
            raise TenantLockError("tenant_id não pode ser alterado para este usuário.")
        if user.tenant_id == new_tenant_id:
            return user
        return user.model_copy(update={"tenant_id": new_tenant_id, "tenant_locked": True})


class ConsultantService:
    """Serviços de domínio específicos para consultores."""

    COMMISSION_RATE_MAX = Decimal("1")
    COMMISSION_RATE_MIN = Decimal("0")

    @classmethod
    def create_consultant(cls, user: UserEntity, data: ConsultantCreateInput) -> ConsultantEntity:
        """Cria entidade de consultor garantindo consistência com o usuário."""

        if user.role is not UserRole.CONSULTANT:
            raise InvalidRoleError("Usuário precisa ter papel CONSULTANT para virar consultor.")
        if user.tenant_id != data.tenant_id:
            raise TenantLockError("Usuário e consultor devem pertencer ao mesmo tenant.")
        if user.id is not None and user.id != data.user_id:
            raise DomainError("Identificador do usuário não corresponde.")

        commission_rate = cls._normalize_rate(data.commission_rate)

        return ConsultantEntity(
            tenant_id=data.tenant_id,
            user_id=data.user_id,
            user=user,
            commission_rate=commission_rate,
            bank_account=data.bank_account,
            is_active_for_loans=data.is_active_for_loans,
        )

    @classmethod
    def set_commission_rate(cls, consultant: ConsultantEntity, rate: Decimal) -> ConsultantEntity:
        """Atualiza a taxa de comissão respeitando limites."""

        normalized = cls._normalize_rate(rate)
        return consultant.model_copy(update={"commission_rate": normalized})

    @classmethod
    def adjust_commission_balance(
        cls,
        consultant: ConsultantEntity,
        adjustment: ConsultantCommissionInput,
    ) -> ConsultantEntity:
        """Ajusta saldo de comissões permitindo débitos/créditos."""

        amount = adjustment.amount
        current = consultant.commission_balance
        new_balance = cls._quantize_money(current + amount)
        return consultant.model_copy(update={"commission_balance": new_balance})

    @classmethod
    def mark_active(cls, consultant: ConsultantEntity) -> ConsultantEntity:
        """Ativa consultor para originar empréstimos."""

        if consultant.is_active_for_loans:
            return consultant
        return consultant.model_copy(update={"is_active_for_loans": True})

    @classmethod
    def mark_inactive(cls, consultant: ConsultantEntity) -> ConsultantEntity:
        """Desativa consultor para originar empréstimos."""

        if not consultant.is_active_for_loans:
            return consultant
        return consultant.model_copy(update={"is_active_for_loans": False})

    @classmethod
    def _normalize_rate(cls, rate: Decimal) -> Decimal:
        if rate < cls.COMMISSION_RATE_MIN or rate > cls.COMMISSION_RATE_MAX:
            raise DomainError("commission_rate deve estar entre 0 e 1.")
        return rate.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    @classmethod
    def _quantize_money(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
