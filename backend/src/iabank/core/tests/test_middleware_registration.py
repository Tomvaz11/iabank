"""
Testes para verificar se o middleware de tenant está corretamente registrado.

Este módulo valida se o TenantIsolationMiddleware foi adequadamente configurado
no settings.py e se está na posição correta na stack de middlewares.
"""

from django.conf import settings
from django.test import TestCase, override_settings


class MiddlewareRegistrationTestCase(TestCase):
    """
    Testes para validar o registro correto do middleware de tenant.

    Verifica se o middleware está presente, na ordem correta, e se pode
    ser instanciado adequadamente pelo Django.
    """

    def test_tenant_middleware_is_registered(self):
        """Verifica se o TenantIsolationMiddleware está registrado em MIDDLEWARE."""
        expected_middleware = 'iabank.core.middleware.TenantIsolationMiddleware'

        self.assertIn(
            expected_middleware,
            settings.MIDDLEWARE,
            f"Middleware {expected_middleware} deve estar presente em MIDDLEWARE"
        )

    def test_tenant_middleware_position(self):
        """Verifica posição correta após AuthenticationMiddleware."""
        middleware_list = settings.MIDDLEWARE
        auth_middleware = 'django.contrib.auth.middleware.AuthenticationMiddleware'
        tenant_middleware = 'iabank.core.middleware.TenantIsolationMiddleware'

        # Verifica se ambos middlewares estão presentes
        self.assertIn(auth_middleware, middleware_list)
        self.assertIn(tenant_middleware, middleware_list)

        # Verifica ordem: TenantIsolationMiddleware vem após AuthenticationMiddleware
        auth_index = middleware_list.index(auth_middleware)
        tenant_index = middleware_list.index(tenant_middleware)

        self.assertGreater(
            tenant_index,
            auth_index,
            "TenantIsolationMiddleware deve vir após AuthenticationMiddleware"
        )

    def test_middleware_can_be_imported(self):
        """Verifica se o middleware pode ser importado sem erros."""
        try:
            from iabank.core.middleware import TenantIsolationMiddleware
            # Tenta instanciar o middleware
            def dummy_get_response(request):
                return None

            middleware_instance = TenantIsolationMiddleware(dummy_get_response)
            self.assertIsNotNone(middleware_instance)

        except ImportError as e:
            self.fail(f"Falha ao importar TenantIsolationMiddleware: {e}")

    def test_middleware_stack_integrity(self):
        """Verifica se todos os middlewares essenciais estão presentes."""
        required_middlewares = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'iabank.core.middleware.TenantIsolationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]

        for middleware in required_middlewares:
            with self.subTest(middleware=middleware):
                self.assertIn(
                    middleware,
                    settings.MIDDLEWARE,
                    f"Middleware essencial {middleware} deve estar presente"
                )

    @override_settings(MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
    ])
    def test_missing_tenant_middleware_detection(self):
        """Verifica que conseguimos detectar quando o middleware não está presente."""
        tenant_middleware = 'iabank.core.middleware.TenantIsolationMiddleware'

        self.assertNotIn(
            tenant_middleware,
            settings.MIDDLEWARE,
            "Test deve confirmar que middleware não está presente quando removido"
        )

    def test_middleware_order_validates_security_requirements(self):
        """Verifica se a ordem dos middlewares atende aos requisitos de segurança."""
        middleware_list = settings.MIDDLEWARE

        # SecurityMiddleware deve ser o primeiro
        self.assertEqual(
            middleware_list[0],
            'django.middleware.security.SecurityMiddleware',
            "SecurityMiddleware deve ser o primeiro middleware"
        )

        # AuthenticationMiddleware deve vir antes do TenantIsolationMiddleware
        auth_pos = middleware_list.index(
            'django.contrib.auth.middleware.AuthenticationMiddleware'
        )
        tenant_pos = middleware_list.index(
            'iabank.core.middleware.TenantIsolationMiddleware'
        )

        self.assertLess(
            auth_pos,
            tenant_pos,
            "AuthenticationMiddleware deve vir antes de TenantIsolationMiddleware"
        )
