"""Tests de integração para o Django admin com filtragem multi-tenant."""
from __future__ import annotations

import pytest
from django.contrib import admin
from django.test import RequestFactory

from iabank.core.factories import TenantFactory
from iabank.customers.admin import CustomerAdmin
from iabank.customers.models import Customer, CustomerDocumentType
from iabank.users.models import User


@pytest.mark.django_db
class TestCustomerAdminTenantFiltering:
    """Valida escopo de tenant no admin de clientes."""

    def setup_method(self):
        self.factory = RequestFactory()
        self.admin = CustomerAdmin(Customer, admin.site)

    def _create_staff_user(self, tenant):
        return User.objects.create_user(
            email=f"admin+{tenant.slug}@example.com",
            password="Adm1nPass!",
            tenant_id=tenant.id,
            is_staff=True,
        )

    def _create_customer(self, tenant, name: str, email: str, document: str):
        return Customer.objects.create(
            tenant_id=tenant.id,
            document_type=CustomerDocumentType.CPF,
            document=document,
            name=name,
            email=email,
            phone="11999999999",
        )

    def _build_request(self, user, tenant_id):
        request = self.factory.get("/admin/customers/customer/")
        request.user = user
        request.tenant_id = tenant_id
        return request

    def test_queryset_filtra_por_tenant_do_usuario(self):
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        user = self._create_staff_user(tenant_a)

        cliente_a = self._create_customer(
            tenant_a,
            name="Cliente A",
            email="cliente.a@example.com",
            document="52998224725",
        )
        self._create_customer(
            tenant_b,
            name="Cliente B",
            email="cliente.b@example.com",
            document="15350946056",
        )

        request = self._build_request(user, tenant_a.id)
        queryset = self.admin.get_queryset(request)

        assert list(queryset) == [cliente_a]

    def test_superuser_visualiza_todos_os_tenants(self):
        tenant_a = TenantFactory()
        tenant_b = TenantFactory()
        superuser = User.objects.create_superuser(
            email="superadmin@example.com",
            password="Sup3rPass!",
            tenant_id=tenant_a.id,
        )

        cliente_a = self._create_customer(
            tenant_a,
            name="Cliente A",
            email="cliente.a@example.com",
            document="52998224725",
        )
        cliente_b = self._create_customer(
            tenant_b,
            name="Cliente B",
            email="cliente.b@example.com",
            document="15350946056",
        )

        request = self._build_request(superuser, tenant_a.id)
        queryset = self.admin.get_queryset(request)

        assert set(queryset) == {cliente_a, cliente_b}
