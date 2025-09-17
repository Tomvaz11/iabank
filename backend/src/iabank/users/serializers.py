"""Serializers para operações de autenticação e gestão de usuários."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from iabank.users.domain.entities import UserEntity, UserRole
from iabank.users.domain.services import (
    DomainError,
    MFAOperationError,
    InvalidRoleError,
    PasswordPolicyError,
    TenantLockError,
    UserCreateInput,
    UserService,
    UserUpdateInput,
)
from iabank.users.models import User


def _map_pydantic_errors(exc: PydanticValidationError) -> Dict[str, List[str]]:
    """Converte erros de validação do Pydantic para formato DRF."""

    errors: Dict[str, List[str]] = {}
    for error in exc.errors():
        loc = error.get("loc") or ("non_field_errors",)
        field = loc[-1] if loc else "non_field_errors"
        errors.setdefault(str(field), []).append(str(error.get("msg")))
    return errors


def _map_integrity_error(exc: IntegrityError) -> Dict[str, List[str]]:
    """Mapeia erros de integridade comuns para mensagens amigáveis."""

    message = str(exc)
    if "users_unique_tenant_email" in message:
        return {"email": ["Usuário com este email já existe no tenant."]}
    if "users_unique_tenant_username" in message:
        return {"username": ["Nome de usuário já está em uso no tenant."]}
    return {"non_field_errors": ["Violação de integridade de dados."]}


def _sync_entity_fields(instance: User, entity: UserEntity, *, fields: Optional[Iterable[str]] = None) -> None:
    """Aplica dados de uma entidade de domínio para o modelo ORM."""

    field_names = list(fields) if fields else [
        "email",
        "first_name",
        "last_name",
        "username",
        "phone_number",
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "mfa_enabled",
        "tenant_id",
        "tenant_locked",
    ]

    for field_name in field_names:
        value = getattr(entity, field_name, None)
        if field_name == "role" and isinstance(value, UserRole):
            value = value.value
        if field_name == "username" and not value:
            value = _fallback_username(str(entity.email))
        if field_name == "phone_number" and value is None:
            value = ""
        if field_name == "mfa_enabled" and value is None:
            value = False
        if field_name == "tenant_id" and value is not None:
            value = uuid.UUID(str(value))
        setattr(instance, field_name, value)

    # Campos derivados dependem de outros atributos
    instance.mfa_secret = entity.mfa_secret or ""


def _fallback_username(email: str) -> str:
    """Gera username padrão a partir do email."""

    local_part = email.split("@", 1)[0] if "@" in email else email
    candidate = local_part[:150] or email[:150]
    return candidate or "usuario"


class UserOutputSerializer(serializers.ModelSerializer):
    """Serializer de leitura alinhado ao contrato público da API."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "mfa_enabled",
            "last_login",
            "created_at",
        )
        read_only_fields = fields


class UserCreateSerializer(serializers.Serializer):
    """Serializer para criação de usuários via domínio."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=[(role.value, role.value) for role in UserRole])
    password = serializers.CharField(min_length=12, write_only=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    is_staff = serializers.BooleanField(required=False, default=False)
    is_superuser = serializers.BooleanField(required=False, default=False)
    mfa_enabled = serializers.BooleanField(required=False, default=False)
    mfa_secret = serializers.CharField(max_length=128, required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id is None:
            raise serializers.ValidationError({
                "tenant": ["Tenant não identificado na requisição (middleware ausente?)."]
            })

        try:
            domain_input = UserCreateInput(
                tenant_id=tenant_id,
                email=attrs["email"],
                password=attrs["password"],
                first_name=attrs.get("first_name"),
                last_name=attrs.get("last_name"),
                username=attrs.get("username"),
                phone_number=attrs.get("phone_number"),
                role=attrs.get("role", UserRole.MANAGER),
                is_staff=attrs.get("is_staff", False),
                is_superuser=attrs.get("is_superuser", False),
                mfa_enabled=attrs.get("mfa_enabled", False),
                mfa_secret=attrs.get("mfa_secret"),
            )
        except PydanticValidationError as exc:
            raise serializers.ValidationError(_map_pydantic_errors(exc)) from exc
        except PasswordPolicyError as exc:
            raise serializers.ValidationError({"password": [str(exc)]}) from exc
        except MFAOperationError as exc:
            raise serializers.ValidationError({"mfa": [str(exc)]}) from exc

        attrs["_domain_input"] = domain_input
        attrs["tenant_id"] = tenant_id
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        domain_input: UserCreateInput = validated_data.pop("_domain_input")
        password = validated_data.pop("password")

        try:
            entity = UserService.create_user(domain_input)
        except PasswordPolicyError as exc:
            raise serializers.ValidationError({"password": [str(exc)]}) from exc

        try:
            user = self._persist_user(entity, password)
        except IntegrityError as exc:
            raise serializers.ValidationError(_map_integrity_error(exc)) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc
        return user

    def _persist_user(self, entity: UserEntity, password: str) -> User:
        username = entity.username or _fallback_username(str(entity.email))
        user = User(
            tenant_id=uuid.UUID(str(entity.tenant_id)),
            email=str(entity.email),
            username=username,
            first_name=entity.first_name or "",
            last_name=entity.last_name or "",
            phone_number=entity.phone_number or "",
            role=entity.role.value if isinstance(entity.role, UserRole) else str(entity.role),
            is_active=entity.is_active,
            is_staff=entity.is_staff,
            is_superuser=entity.is_superuser,
            date_joined=entity.date_joined,
            mfa_enabled=entity.mfa_enabled,
            tenant_locked=entity.tenant_locked,
        )
        user.set_password(password)
        user.mfa_secret = entity.mfa_secret or ""
        user.full_clean()
        user.save()
        return user


class UserUpdateSerializer(serializers.Serializer):
    """Serializer para atualização parcial de usuários via domínio."""

    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    role = serializers.ChoiceField(
        choices=[(role.value, role.value) for role in UserRole], required=False
    )
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    mfa_enabled = serializers.BooleanField(required=False)
    mfa_secret = serializers.CharField(max_length=128, required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            domain_input = UserUpdateInput(**attrs)
        except PydanticValidationError as exc:
            raise serializers.ValidationError(_map_pydantic_errors(exc)) from exc
        except MFAOperationError as exc:
            raise serializers.ValidationError({"mfa": [str(exc)]}) from exc

        attrs["_domain_input"] = domain_input
        return attrs

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        domain_input: UserUpdateInput = validated_data.pop("_domain_input")
        current_entity = UserEntity.model_validate(instance)

        try:
            updated_entity = UserService.update_user(current_entity, domain_input)
        except MFAOperationError as exc:
            raise serializers.ValidationError({"mfa": [str(exc)]}) from exc
        except TenantLockError as exc:
            raise serializers.ValidationError({"tenant": [str(exc)]}) from exc
        except InvalidRoleError as exc:
            raise serializers.ValidationError({"role": [str(exc)]}) from exc
        except PasswordPolicyError as exc:
            raise serializers.ValidationError({"password": [str(exc)]}) from exc
        except DomainError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc

        _sync_entity_fields(instance, updated_entity)
        instance.full_clean()
        instance.save()
        return instance
