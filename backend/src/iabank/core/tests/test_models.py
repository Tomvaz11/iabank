"""
Testes unitários para os modelos do app core.

Este módulo contém os testes unitários para validação dos modelos Tenant, User
e BaseTenantModel, garantindo que a funcionalidade multi-tenant esteja
funcionando corretamente. 

Atualizado para usar factory-boy conforme Blueprint Diretriz 15.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import BaseTenantModel, Tenant
from .factories import AdminUserFactory, TenantFactory, UserFactory

User = get_user_model()


class TenantModelTestCase(TestCase):
    """Testes para o modelo Tenant usando factory-boy."""

    def test_tenant_creation(self):
        """Testa a criação básica de um tenant via factory."""
        tenant = TenantFactory(name="Tenant Teste")

        self.assertEqual(tenant.name, "Tenant Teste")
        self.assertTrue(tenant.is_active)
        self.assertIsNotNone(tenant.created_at)
        self.assertIsNotNone(tenant.updated_at)

    def test_tenant_str_representation(self):
        """Testa a representação em string do tenant."""
        tenant = TenantFactory(name="Minha Empresa")
        self.assertEqual(str(tenant), "Minha Empresa")

    def test_tenant_ordering(self):
        """Testa a ordenação padrão dos tenants por nome."""
        TenantFactory(name="B Tenant")
        TenantFactory(name="A Tenant")  
        TenantFactory(name="C Tenant")

        tenants = list(Tenant.objects.all())
        self.assertEqual(tenants[0].name, "A Tenant")
        self.assertEqual(tenants[1].name, "B Tenant")
        self.assertEqual(tenants[2].name, "C Tenant")

    def test_tenant_meta_attributes(self):
        """Testa os atributos Meta do modelo Tenant."""
        self.assertEqual(Tenant._meta.db_table, 'core_tenant')
        self.assertEqual(Tenant._meta.verbose_name, 'Tenant')
        self.assertEqual(Tenant._meta.verbose_name_plural, 'Tenants')

    def test_tenant_is_active_default(self):
        """Testa se is_active é True por padrão."""
        tenant = TenantFactory()
        self.assertTrue(tenant.is_active)


class UserModelTestCase(TestCase):
    """Testes para o modelo User customizado usando factory-boy."""

    def test_user_creation_with_tenant(self):
        """Testa criação de usuário com tenant via factory."""
        tenant = TenantFactory()
        user = UserFactory(tenant=tenant)

        self.assertEqual(user.tenant, tenant)
        self.assertIsNotNone(user.username)
        self.assertIsNotNone(user.email)
        self.assertTrue(user.is_active)

    def test_user_str_representation(self):
        """Testa representação em string do usuário."""
        user = UserFactory(username="testuser")
        # User representation inclui tenant, então verificar se username está presente
        self.assertIn("testuser", str(user))

    def test_user_tenant_relationship(self):
        """Testa o relacionamento User -> Tenant."""
        tenant = TenantFactory(name="Empresa Test")
        user = UserFactory(tenant=tenant)

        self.assertEqual(user.tenant.name, "Empresa Test")
        self.assertIn(user, tenant.users.all())

    def test_user_meta_attributes(self):
        """Testa os atributos Meta do modelo User."""
        self.assertEqual(User._meta.db_table, 'core_user')

    def test_user_cascade_delete_with_tenant(self):
        """Testa que usuário é deletado quando tenant é deletado (CASCADE)."""
        tenant = TenantFactory()
        user = UserFactory(tenant=tenant)
        user_id = user.id
        
        # Deletar tenant deve deletar usuário em cascata
        tenant.delete()
        
        # Usuário deve ter sido deletado
        self.assertFalse(User.objects.filter(id=user_id).exists())


class BaseTenantModelTestCase(TestCase):
    """Testes para o modelo abstrato BaseTenantModel."""

    def test_base_tenant_model_is_abstract(self):
        """Testa que BaseTenantModel é um modelo abstrato."""
        self.assertTrue(BaseTenantModel._meta.abstract)

    def test_base_tenant_model_fields(self):
        """Testa os campos do BaseTenantModel."""
        fields = [f.name for f in BaseTenantModel._meta.fields]
        
        self.assertIn('tenant', fields)
        self.assertIn('created_at', fields)
        self.assertIn('updated_at', fields)

    def test_base_tenant_model_tenant_field(self):
        """Testa as propriedades do campo tenant."""
        tenant_field = BaseTenantModel._meta.get_field('tenant')
        
        self.assertEqual(tenant_field.related_model, Tenant)
        # Verificar que on_delete é CASCADE comparando com a função
        from django.db.models import CASCADE
        self.assertEqual(tenant_field.remote_field.on_delete, CASCADE)

    def test_base_tenant_model_timestamp_fields(self):
        """Testa as propriedades dos campos de timestamp."""
        created_at_field = BaseTenantModel._meta.get_field('created_at')
        updated_at_field = BaseTenantModel._meta.get_field('updated_at')
        
        self.assertTrue(created_at_field.auto_now_add)
        self.assertTrue(updated_at_field.auto_now)

    def test_concrete_model_inheriting_base_tenant_model(self):
        """
        Testa que um modelo concreto herda corretamente de BaseTenantModel.
        
        Este teste usa o modelo User que herda de AbstractUser, mas validamos
        que BaseTenantModel funciona corretamente para herança futura.
        """
        # Criar modelo de teste em tempo de execução
        from django.db import models
        
        class TestModel(BaseTenantModel):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'core'
        
        # Verificar herança
        fields = [f.name for f in TestModel._meta.fields]
        self.assertIn('tenant', fields)
        self.assertIn('created_at', fields)
        self.assertIn('updated_at', fields)
        self.assertIn('name', fields)


class FactoryIntegrationTestCase(TestCase):
    """Testes de integração das factories com os modelos."""

    def test_tenant_factory_integration(self):
        """Testa integração entre TenantFactory e modelo Tenant."""
        tenant = TenantFactory()
        
        # Verificar que foi salvo no banco
        self.assertTrue(Tenant.objects.filter(id=tenant.id).exists())
        
        # Verificar campos obrigatórios
        self.assertIsNotNone(tenant.name)
        self.assertTrue(tenant.is_active)

    def test_user_factory_integration(self):
        """Testa integração entre UserFactory e modelo User."""
        user = UserFactory()
        
        # Verificar que foi salvo no banco
        self.assertTrue(User.objects.filter(id=user.id).exists())
        
        # Verificar relacionamento com tenant
        self.assertIsNotNone(user.tenant)
        self.assertTrue(Tenant.objects.filter(id=user.tenant.id).exists())

    def test_admin_user_factory_integration(self):
        """Testa integração da AdminUserFactory."""
        admin = AdminUserFactory()
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertIsNotNone(admin.tenant)

    def test_multiple_users_same_tenant_via_factory(self):
        """Testa criação de múltiplos usuários no mesmo tenant via factory."""
        tenant = TenantFactory()
        user1 = UserFactory(tenant=tenant)
        user2 = UserFactory(tenant=tenant)
        admin = AdminUserFactory(tenant=tenant)
        
        # Todos devem estar no mesmo tenant
        self.assertEqual(user1.tenant, tenant)
        self.assertEqual(user2.tenant, tenant)
        self.assertEqual(admin.tenant, tenant)
        
        # Mas devem ser usuários diferentes
        self.assertNotEqual(user1.id, user2.id)
        self.assertNotEqual(user1.username, user2.username)