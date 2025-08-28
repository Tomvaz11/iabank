"""
Meta-testes para as factories do app core.

Este módulo implementa os testes obrigatórios conforme Blueprint Diretriz 15:
"Para cada factories.py, um arquivo test_factories.py deve existir para validar
a consistência dos dados gerados", especialmente a propagação correta de tenant.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from .factories import AdminUserFactory, TenantFactory, UserFactory
from ..models import Tenant

User = get_user_model()


class CoreFactoriesTestCase(TestCase):
    """Meta-testes para validar factories do core."""

    def test_tenant_factory_creates_valid_tenant(self):
        """Testa se TenantFactory cria tenants válidos."""
        tenant = TenantFactory()
        
        self.assertIsInstance(tenant, Tenant)
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.name)
        self.assertIsNotNone(tenant.created_at)
        self.assertIsNotNone(tenant.updated_at)

    def test_tenant_factory_uniqueness(self):
        """Testa se TenantFactory gera nomes únicos."""
        tenant1 = TenantFactory()
        tenant2 = TenantFactory()
        
        self.assertNotEqual(tenant1.name, tenant2.name)
        self.assertNotEqual(tenant1.id, tenant2.id)

    def test_user_factory_creates_valid_user(self):
        """Testa se UserFactory cria usuários válidos."""
        user = UserFactory()
        
        self.assertIsInstance(user, User)
        self.assertIsInstance(user.tenant, Tenant)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)

    def test_user_factory_tenant_consistency(self):
        """
        Testa propagação de tenant - CRÍTICO para multi-tenancy.
        
        Este é o teste mais importante conforme Blueprint:
        garantir que o tenant seja corretamente propagado.
        """
        # Criar tenant específico
        tenant = TenantFactory()
        
        # Criar usuário com esse tenant
        user = UserFactory(tenant=tenant)
        
        # Verificar propagação
        self.assertEqual(user.tenant, tenant)
        self.assertEqual(user.tenant.id, tenant.id)

    def test_admin_user_factory_creates_admin(self):
        """Testa se AdminUserFactory cria administradores válidos."""
        admin = AdminUserFactory()
        
        self.assertIsInstance(admin, User)
        self.assertIsInstance(admin.tenant, Tenant)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_admin_user_factory_tenant_consistency(self):
        """Testa propagação de tenant para admin user."""
        tenant = TenantFactory()
        admin = AdminUserFactory(tenant=tenant)
        
        self.assertEqual(admin.tenant, tenant)

    def test_multiple_users_same_tenant(self):
        """
        Testa cenário multi-tenant: múltiplos usuários no mesmo tenant.
        
        Este teste valida o padrão fundamental do sistema multi-tenant.
        """
        tenant = TenantFactory()
        user1 = UserFactory(tenant=tenant)
        user2 = UserFactory(tenant=tenant)
        admin = AdminUserFactory(tenant=tenant)
        
        # Todos devem pertencer ao mesmo tenant
        self.assertEqual(user1.tenant, tenant)
        self.assertEqual(user2.tenant, tenant) 
        self.assertEqual(admin.tenant, tenant)
        
        # Mas devem ser usuários diferentes
        self.assertNotEqual(user1.id, user2.id)
        self.assertNotEqual(user1.username, user2.username)

    def test_factories_with_default_tenant_creation(self):
        """Testa se factories criam tenant automaticamente quando não especificado."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Cada user deve ter seu próprio tenant quando não especificado
        self.assertNotEqual(user1.tenant.id, user2.tenant.id)
        self.assertIsNotNone(user1.tenant)
        self.assertIsNotNone(user2.tenant)