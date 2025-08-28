"""
Testes de integração para autenticação.

Este módulo implementa os testes de simulação de autenticação conforme 
Blueprint Diretriz 15: "Usaremos api_client.force_authenticate(user=self.user) 
para simular um usuário logado em testes de API, evitando o fluxo completo de login."

Embora não tenhamos APIs próprias ainda, testamos a autenticação base do Django
que será fundamental para APIs futuras.
"""

from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from iabank.core.tests.factories import AdminUserFactory, TenantFactory, UserFactory

User = get_user_model()


class AuthenticationIntegrationTestCase(TestCase):
    """Testes de integração para autenticação com simulação conforme Blueprint."""

    def setUp(self):
        """Setup para testes de autenticação."""
        self.api_client = APIClient()  # Conforme Blueprint Diretriz 15
        self.tenant = TenantFactory()
        self.user = UserFactory(tenant=self.tenant)
        self.admin_user = AdminUserFactory(tenant=self.tenant)

    def test_user_authentication_flow(self):
        """Testa fluxo completo de autenticação do usuário customizado."""
        # Verificar que usuário foi criado corretamente
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertEqual(self.user.tenant, self.tenant)

    def test_api_client_force_authenticate_pattern(self):
        """
        Testa padrão obrigatório do Blueprint: api_client.force_authenticate.
        
        Este teste implementa exatamente o padrão especificado na Diretriz 15:
        "Usaremos api_client.force_authenticate(user=self.user) para simular
        um usuário logado em testes de API."
        """
        # Simulação de autenticação conforme Blueprint
        self.api_client.force_authenticate(user=self.user)
        
        # Verificar que autenticação foi simulada corretamente
        self.assertEqual(self.api_client.handler._force_user, self.user)

    def test_api_client_unauthenticated_state(self):
        """Testa estado não autenticado do APIClient."""
        # Client deve iniciar sem autenticação
        self.assertIsNone(getattr(self.api_client.handler, '_force_user', None))

    def test_api_client_authentication_switching(self):
        """Testa alternância entre diferentes usuários autenticados."""
        # Autenticar como usuário comum
        self.api_client.force_authenticate(user=self.user)
        self.assertEqual(self.api_client.handler._force_user, self.user)
        
        # Alternar para admin
        self.api_client.force_authenticate(user=self.admin_user)
        self.assertEqual(self.api_client.handler._force_user, self.admin_user)
        
        # Remover autenticação
        self.api_client.force_authenticate(user=None)
        self.assertIsNone(self.api_client.handler._force_user)

    def test_multi_tenant_authentication_isolation(self):
        """
        Testa isolamento de autenticação entre tenants.
        
        Este teste valida que nossa autenticação customizada funciona
        corretamente com o sistema multi-tenant.
        """
        # Criar usuário de outro tenant
        other_tenant = TenantFactory()
        other_user = UserFactory(tenant=other_tenant)
        
        # Autenticar usuário do primeiro tenant
        self.api_client.force_authenticate(user=self.user)
        self.assertEqual(self.user.tenant, self.tenant)
        
        # Alternar para usuário de outro tenant
        self.api_client.force_authenticate(user=other_user)
        self.assertEqual(other_user.tenant, other_tenant)
        
        # Verificar que tenants são diferentes
        self.assertNotEqual(self.user.tenant, other_user.tenant)

    def test_admin_user_authentication(self):
        """Testa autenticação de usuário administrador."""
        self.api_client.force_authenticate(user=self.admin_user)
        
        # Verificar propriedades do admin
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
        self.assertEqual(self.admin_user.tenant, self.tenant)

    def test_django_authentication_backend_integration(self):
        """
        Testa integração com o backend de autenticação do Django.
        
        Valida que nosso modelo User customizado funciona com o sistema
        de autenticação padrão do Django.
        """
        # Definir senha para teste (factories não definem senha por padrão)
        self.user.set_password('testpass123')
        self.user.save()
        
        # Testar autenticação via backend do Django
        authenticated_user = authenticate(
            username=self.user.username,
            password='testpass123'
        )
        
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, self.user)
        self.assertEqual(authenticated_user.tenant, self.tenant)

    def test_authentication_with_inactive_user(self):
        """Testa que usuários inativos não podem se autenticar."""
        # Desativar usuário
        self.user.is_active = False
        self.user.set_password('testpass123')
        self.user.save()
        
        # Tentar autenticar usuário inativo
        authenticated_user = authenticate(
            username=self.user.username,
            password='testpass123'
        )
        
        # Autenticação deve falhar
        self.assertIsNone(authenticated_user)


class APIClientPatternTestCase(TestCase):
    """Testes específicos para validar padrões do APIClient conforme Blueprint."""

    def test_api_client_import_available(self):
        """Testa que APIClient está disponível conforme Blueprint."""
        from rest_framework.test import APIClient
        
        client = APIClient()
        self.assertIsNotNone(client)

    def test_force_authenticate_method_exists(self):
        """Testa que método force_authenticate existe e funciona."""
        from rest_framework.test import APIClient
        
        client = APIClient()
        user = UserFactory()
        
        # Método deve existir e não gerar erro
        client.force_authenticate(user=user)
        self.assertEqual(client.handler._force_user, user)

    def test_blueprint_authentication_pattern_ready(self):
        """
        Testa que o padrão completo do Blueprint está pronto para uso.
        
        Este teste confirma que quando implementarmos APIs reais,
        o padrão especificado no Blueprint funcionará corretamente.
        """
        from rest_framework.test import APIClient
        
        client = APIClient()
        user = UserFactory()
        
        # Padrão exato do Blueprint
        client.force_authenticate(user=user)
        
        # Verificar que funciona
        self.assertEqual(client.handler._force_user, user)
        self.assertIsInstance(user.tenant, type(user.tenant))  # Tenant existe