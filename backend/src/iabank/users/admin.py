"""Admin do aplicativo de usuários com filtragem por tenant."""
from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from iabank.core.admin import TenantScopedAdminMixin

from .models import Consultant, User


class TenantUserCreationForm(forms.ModelForm):
    """Formulário customizado para criação de usuários via admin."""

    password1 = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmação de senha", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone_number", "role")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem.")
        return password2

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class TenantUserChangeForm(forms.ModelForm):
    """Formulário de edição exibindo hash de senha como somente leitura."""

    password = ReadOnlyPasswordHashField(label="Senha")

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "is_staff",
            "is_superuser",
            "mfa_enabled",
            "tenant_id",
            "groups",
            "user_permissions",
        )

    def clean_password(self):
        return self.initial.get("password")


@admin.register(User)
class TenantUserAdmin(TenantScopedAdminMixin, DjangoUserAdmin):
    """Admin multi-tenant para o modelo de usuários."""

    add_form = TenantUserCreationForm
    form = TenantUserChangeForm
    model = User
    list_display = (
        "email",
        "role",
        "is_active",
        "is_staff",
        "last_login",
        "tenant_id",
    )
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "mfa_enabled",
    )
    search_fields = ("email", "login_identifier", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = (
        "login_identifier",
        "tenant_locked",
        "last_login",
        "date_joined",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Informações pessoais",
            {"fields": ("first_name", "last_name", "phone_number")},
        ),
        (
            "Permissões",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "mfa_enabled",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Tenant",
            {"fields": ("tenant_id", "tenant_locked", "login_identifier")},
        ),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Consultant)
class ConsultantAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    """Admin multi-tenant para consultores."""

    list_display = (
        "user",
        "commission_rate",
        "commission_balance",
        "is_active_for_loans",
        "tenant_id",
    )
    list_filter = ("is_active_for_loans",)
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("tenant_id",)


__all__ = ["TenantUserAdmin", "ConsultantAdmin"]
