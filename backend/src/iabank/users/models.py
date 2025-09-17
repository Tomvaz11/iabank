"""Modelos do app de usuários."""
from __future__ import annotations

import uuid
from typing import Optional, Tuple

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from iabank.core.fields import EncryptedCharField
from iabank.core.models import BaseTenantModel, Tenant


class UserRole(models.TextChoices):
    """Enum de papéis suportados pelo sistema."""

    ADMIN = "ADMIN", "Administrador"
    MANAGER = "MANAGER", "Gestor"
    CONSULTANT = "CONSULTANT", "Consultor"
    COLLECTOR = "COLLECTOR", "Cobrança"
    FINANCE_MANAGER = "FINANCE_MANAGER", "Gestor Financeiro"
    FINANCE_ANALYST = "FINANCE_ANALYST", "Analista Financeiro"
    COMPLIANCE_MANAGER = "COMPLIANCE_MANAGER", "Gestor de Compliance"


class UserManager(BaseUserManager):
    """Manager customizado aplicando regras multi-tenant."""

    use_in_migrations = True

    def _resolve_tenant_assignment(
        self,
        *,
        tenant: Optional[Tenant] = None,
        tenant_id: Optional[uuid.UUID | str] = None,
    ) -> Tuple[uuid.UUID, bool]:
        """Resolve tenant_id e se o vínculo deve ser bloqueado imediatamente."""

        if tenant and tenant_id:
            raise ValueError("Informe tenant ou tenant_id, não ambos")

        if tenant is not None:
            return tenant.id, True

        if tenant_id is not None:
            if isinstance(tenant_id, uuid.UUID):
                return tenant_id, True
            return uuid.UUID(str(tenant_id)), True

        # Tenta obter do contexto (requests/testes)
        try:
            from iabank.core.middleware import TenantMiddleware

            current_tenant = TenantMiddleware.get_current_tenant()
        except Exception:  # pragma: no cover - fallback defensive
            current_tenant = None

        if current_tenant is not None:
            return current_tenant.id, True

        # Fallback: utiliza primeiro tenant existente (útil em testes setUp)
        fallback_id = (
            Tenant.objects.order_by("created_at")
            .values_list("id", flat=True)
            .first()
        )
        if fallback_id:
            return uuid.UUID(str(fallback_id)), False

        raise ValueError("tenant_id é obrigatório para criar usuários")

    def _create_user(self, email: str, password: Optional[str], **extra_fields):
        if not email:
            raise ValueError("Email é obrigatório")

        email = self.normalize_email(email)
        tenant = extra_fields.pop("tenant", None)
        tenant_id_field = extra_fields.pop("tenant_id", None)

        tenant_uuid, lock_on_create = self._resolve_tenant_assignment(
            tenant=tenant,
            tenant_id=tenant_id_field,
        )

        username = extra_fields.get("username")
        if username is None:
            # Mantém compatibilidade com testes que ainda enviam username
            username = email.split("@")[0][:150]
            extra_fields["username"] = username

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", UserRole.MANAGER)

        user = self.model(**extra_fields)
        user.email = email
        user.tenant_id = tenant_uuid
        user.tenant_locked = lock_on_create
        user.login_identifier = self.model.build_login_identifier(tenant_uuid, email)
        user.set_password(password)

        # Valida campos principais antes de persistir
        user.full_clean(exclude=["password"])

        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields):
        """Cria usuário regular com role padrão MANAGER."""

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        """Cria superuser exigindo flags administrativas."""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário deve ter is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário deve ter is_superuser=True")

        return self._create_user(email, password, **extra_fields)


class User(BaseTenantModel, AbstractBaseUser, PermissionsMixin):
    """Modelo de usuário multi-tenant com RBAC."""

    email = models.EmailField(
        "email address",
        max_length=254,
        help_text="Email corporativo do usuário",
    )
    login_identifier = models.CharField(
        max_length=255,
        unique=True,
        editable=False,
        help_text="Identificador global único (tenant + email)",
    )
    username = models.CharField(
        "username",
        max_length=150,
        validators=[validators.RegexValidator(r"^[\w.@+-]+$")],
        blank=True,
        null=True,
        help_text="Identificador curto opcional",
    )
    first_name = models.CharField(
        "first name",
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        "last name",
        max_length=150,
        blank=True,
    )
    phone_number = models.CharField(
        max_length=32,
        blank=True,
        help_text="Telefone de contato com DDI/DDI",
    )
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.MANAGER,
        help_text="Papel do usuário na hierarquia RBAC",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Permite acesso ao Django admin",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se o usuário está ativo",
    )
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Data de cadastro do usuário",
    )
    mfa_enabled = models.BooleanField(
        default=False,
        help_text="Indica se MFA está habilitado para o usuário",
    )
    mfa_secret = EncryptedCharField(
        max_length=128,
        blank=True,
        help_text="Segredo TOTP criptografado",
    )
    tenant_locked = models.BooleanField(
        default=False,
        editable=False,
        help_text="Controle interno para impedir troca de tenant",
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "login_identifier"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        indexes = [
            models.Index(
                fields=["tenant_id", "email"],
                name="users_tenant_email_idx",
            ),
            models.Index(
                fields=["tenant_id", "role"],
                name="users_tenant_role_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "email"],
                name="users_unique_tenant_email",
            ),
            models.UniqueConstraint(
                fields=["tenant_id", "username"],
                name="users_unique_tenant_username",
            ),
        ]

    def clean(self):
        super().clean()

        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

        if self.username:
            self.username = self.username.strip()

        if self.role:
            self.role = self.role.upper()

        if self.tenant_id and self.email:
            self.login_identifier = self.build_login_identifier(self.tenant_id, self.email)

        if self.mfa_enabled and not self.mfa_secret:
            raise ValidationError({"mfa_secret": "Segredo MFA é obrigatório quando MFA estiver habilitado."})

        if not self.mfa_enabled:
            # Remove segredo se MFA estiver desativado
            self.mfa_secret = ""

    def save(self, *args, **kwargs):
        if self.pk:
            current = (
                self.__class__._default_manager.filter(pk=self.pk)
                .values_list("tenant_id", "tenant_locked")
                .first()
            )
            if current:
                original_tenant_id, tenant_locked = current
                if original_tenant_id and self.tenant_id:
                    original_uuid = uuid.UUID(str(original_tenant_id))
                    current_uuid = uuid.UUID(str(self.tenant_id))
                    if original_uuid != current_uuid:
                        if tenant_locked:
                            raise ValueError("tenant_id não pode ser alterado para este usuário")
                        # Permite uma única atualização controlada
                        self._allow_tenant_override = True
                        self.tenant_locked = True

        if self.tenant_id and self.email:
            self.login_identifier = self.build_login_identifier(self.tenant_id, self.email)

        return super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        """Retorna nome completo."""

        full_name = f"{(self.first_name or '').strip()} {(self.last_name or '').strip()}".strip()
        return full_name or (self.username or self.email)

    def get_short_name(self) -> str:
        """Retorna nome curto para exibição."""

        return (self.first_name or self.username or self.email).strip()

    @staticmethod
    def build_login_identifier(tenant_id: uuid.UUID, email: str) -> str:
        """Cria identificador único combinando tenant_id e email normalizado."""

        if not tenant_id or not email:
            raise ValueError("tenant_id e email são obrigatórios para login_identifier")
        return f"{uuid.UUID(str(tenant_id))}:{email.strip().lower()}"

    @property
    def tenant(self) -> Optional[Tenant]:
        """Retorna instância de Tenant associada (lazy)."""

        if not self.tenant_id:
            return None
        return Tenant.objects.filter(id=self.tenant_id).first()

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "email": self.email,
                "role": self.role,
                "is_active": self.is_active,
            }
        )
        return fields

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"
