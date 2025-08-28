"""
Testes de validação para verificar o registro correto da app iabank.core em settings.py.

Este módulo testa especificamente o Alvo 2 da implementação: garantir que a app
iabank.core está corretamente registrada no INSTALLED_APPS do Django.
"""

from django.apps import apps
from django.conf import settings
from django.test import TestCase


class CoreAppRegistrationTestCase(TestCase):
    """Testes para validar o registro da app iabank.core em settings.py."""

    def test_core_app_in_installed_apps(self):
        """Testa se 'iabank.core' está presente em INSTALLED_APPS."""
        self.assertIn(
            'iabank.core',
            settings.INSTALLED_APPS,
            "A app 'iabank.core' deve estar registrada em INSTALLED_APPS"
        )

    def test_core_app_config_loaded(self):
        """Testa se a configuração da app core foi carregada corretamente."""
        try:
            core_app_config = apps.get_app_config('core')
            self.assertEqual(
                core_app_config.name,
                'iabank.core',
                "A configuração da app core deve ter o nome 'iabank.core'"
            )
        except LookupError:
            self.fail("A app 'core' não foi encontrada nas apps carregadas pelo Django")

    def test_core_app_models_accessible(self):
        """Testa se os modelos da app core estão acessíveis."""
        try:
            from iabank.core.models import BaseTenantModel, Tenant, User
            # Verificar se conseguimos acessar os modelos
            self.assertTrue(
                hasattr(Tenant, 'name'), "Modelo Tenant deve ter campo 'name'"
            )
            self.assertTrue(
                hasattr(User, 'tenant'), "Modelo User deve ter campo 'tenant'"
            )
            self.assertTrue(
                hasattr(BaseTenantModel, '_meta'),
                "BaseTenantModel deve ser um modelo Django"
            )
        except ImportError as e:
            self.fail(f"Modelos da app core não estão acessíveis: {e}")

    def test_core_app_admin_integration(self):
        """Testa se a integração com o Django Admin está funcionando."""
        from django.contrib import admin

        from iabank.core.models import Tenant, User

        # Verificar se os modelos estão registrados no admin
        self.assertIn(
            Tenant,
            admin.site._registry,
            "Modelo Tenant deve estar registrado no Django Admin"
        )
        self.assertIn(
            User,
            admin.site._registry,
            "Modelo User deve estar registrado no Django Admin"
        )

    def test_core_app_in_local_apps(self):
        """Testa se iabank.core está na seção LOCAL_APPS do settings."""
        # Acessar a configuração LOCAL_APPS se estiver definida
        local_apps = getattr(settings, 'LOCAL_APPS', [])
        if local_apps:
            self.assertIn(
                'iabank.core',
                local_apps,
                "A app 'iabank.core' deve estar em LOCAL_APPS"
            )

    def test_custom_user_model_setting(self):
        """Testa se AUTH_USER_MODEL está configurado corretamente para core.User."""
        self.assertEqual(
            settings.AUTH_USER_MODEL,
            'core.User',
            "AUTH_USER_MODEL deve apontar para 'core.User'"
        )

    def test_apps_registry_consistency(self):
        """Testa se o registro da app é consistente em todo o Django."""
        # Verificar se a app está no registry global
        self.assertTrue(
            apps.is_installed('iabank.core'),
            "A app 'iabank.core' deve estar instalada no registry do Django"
        )

        # Verificar se podemos obter a configuração da app
        app_config = apps.get_app_config('core')
        self.assertIsNotNone(
            app_config,
            "Deve ser possível obter a configuração da app core"
        )

    def test_migrations_directory_accessible(self):
        """Testa se o diretório de migrações está acessível."""
        import os

        from django.apps import apps

        app_config = apps.get_app_config('core')
        migrations_path = os.path.join(app_config.path, 'migrations')

        self.assertTrue(
            os.path.exists(migrations_path),
            "Diretório de migrações deve existir para a app core"
        )

        # Verificar se a migração inicial existe
        initial_migration = os.path.join(migrations_path, '0001_initial.py')
        self.assertTrue(
            os.path.exists(initial_migration),
            "Migração inicial 0001_initial.py deve existir"
        )


class CoreAppIntegrationTestCase(TestCase):
    """Testes de integração para validar o funcionamento da app registrada."""

    def test_can_create_tenant_through_orm(self):
        """Testa se é possível criar um Tenant usando o ORM Django."""
        from iabank.core.models import Tenant

        tenant = Tenant.objects.create(name="Test Tenant")
        self.assertIsNotNone(tenant.pk, "Tenant deve ser criado com sucesso")
        self.assertEqual(tenant.name, "Test Tenant")

    def test_can_create_user_through_orm(self):
        """Testa se é possível criar um User usando o ORM Django."""
        from iabank.core.models import Tenant, User

        tenant = Tenant.objects.create(name="Test Tenant")
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            tenant=tenant
        )

        self.assertIsNotNone(user.pk, "User deve ser criado com sucesso")
        self.assertEqual(user.tenant, tenant)

    def test_database_tables_created(self):
        """Testa se as tabelas do banco de dados foram criadas."""
        from django.db import connection

        with connection.cursor() as cursor:
            # Obter todas as tabelas
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE 'core_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]

        self.assertIn(
            'core_tenant',
            tables,
            "Tabela core_tenant deve existir no banco de dados"
        )
        self.assertIn(
            'core_user',
            tables,
            "Tabela core_user deve existir no banco de dados"
        )
