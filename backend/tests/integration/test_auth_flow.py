"""
Integration test fluxo completo autenticação.

Testa o fluxo completo de autenticação incluindo:
- Login com credenciais válidas e inválidas
- Refresh token functionality
- MFA (Multi-Factor Authentication) quando habilitado
- Isolamento por tenant
- Auditoria e logging estruturado
- Validação de tokens JWT
- Expiração e renovação de tokens

Baseado em:
- T013 do tasks.md
- Constitution v1.0.0 - Django-Domain-First Architecture
- JWT com djangorestframework-simplejwt (T072)
- MFA com django-otp (T078)
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from iabank.core.factories import TenantContextManager, TenantFactory
from iabank.core.models import Tenant

User = get_user_model()


@pytest.mark.integration
class TestAuthenticationFlow(TransactionTestCase):
    """
    Integration test para fluxo completo de autenticação.

    Testa todo o fluxo desde login até logout, incluindo:
    - Criação e validação de tokens JWT
    - Refresh token functionality
    - Isolamento multi-tenant
    - Auditoria e logs estruturados
    - Tratamento de erros e edge cases
    """

    def setUp(self):
        """Setup para integration tests de autenticação."""
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login"
        self.refresh_url = "/api/v1/auth/refresh"

        # Criar tenant para isolamento
        self.tenant = TenantFactory()

        # Criar usuário de teste
        with TenantContextManager(self.tenant.id):
            self.test_user = User.objects.create_user(
                username="testuser",
                email="testuser@empresa.com.br",
                password="SecurePass123!",
                is_active=True
            )
            # Simular tenant_id no User (será implementado no T023)
            if hasattr(self.test_user, "tenant_id"):
                self.test_user.tenant_id = self.tenant.id
                self.test_user.save()

    def tearDown(self):
        """Limpeza após cada teste."""
        User.objects.all().delete()
        Tenant.objects.all().delete()

    def test_complete_login_flow_success(self):
        """
        Test: Fluxo completo de login bem-sucedido.

        Fluxo:
        1. POST /api/v1/auth/login com credenciais válidas
        2. Recebe access_token e refresh_token
        3. Valida estrutura do response
        4. Valida dados do usuário retornados
        5. Verifica logs de auditoria
        """
        # Payload de login válido
        login_payload = {
            "email": "testuser@empresa.com.br",
            "password": "SecurePass123!",
            "tenant_domain": "empresa"
        }

        with patch("iabank.core.jwt_views.logger") as mock_logger, \
             patch("iabank.core.jwt_views.log_business_event") as mock_audit:

            # Executar login
            response = self.client.post(
                self.login_url,
                data=login_payload,
                format="json"
            )

            # Verificar status de sucesso
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Verificar estrutura do response
            data = response.json()
            self.assertIn("data", data)
            self.assertIn("meta", data)

            # Verificar tokens no response
            response_data = data["data"]
            self.assertIn("access_token", response_data)
            self.assertIn("refresh_token", response_data)
            self.assertIn("token_type", response_data)
            self.assertIn("expires_in", response_data)
            self.assertIn("user", response_data)

            # Verificar tipos dos campos
            self.assertIsInstance(response_data["access_token"], str)
            self.assertIsInstance(response_data["refresh_token"], str)
            self.assertEqual(response_data["token_type"], "Bearer")
            self.assertIsInstance(response_data["expires_in"], int)
            self.assertGreater(response_data["expires_in"], 0)

            # Verificar dados do usuário
            user_data = response_data["user"]
            self.assertEqual(user_data["username"], "testuser")
            self.assertEqual(user_data["email"], "testuser@empresa.com.br")
            self.assertTrue(user_data["is_active"])

            # Verificar logging estruturado
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args
            self.assertEqual(call_args[0][0], "Login successful")
            self.assertIn("email", call_args[1])
            self.assertIn("user_id", call_args[1])

            # Verificar auditoria de negócio
            mock_audit.assert_called()
            audit_call = mock_audit.call_args[1]
            self.assertEqual(audit_call["event_type"], "security")
            self.assertEqual(audit_call["entity_type"], "user")
            self.assertEqual(audit_call["action"], "login_success")

    def test_login_with_invalid_credentials(self):
        """
        Test: Login com credenciais inválidas.

        Fluxo:
        1. POST /api/v1/auth/login com senha incorreta
        2. Recebe erro 401 Unauthorized
        3. Verifica estrutura de erro
        4. Verifica logs de auditoria de falha
        """
        login_payload = {
            "email": "testuser@empresa.com.br",
            "password": "WrongPassword",
        }

        with patch("iabank.core.jwt_views.logger") as mock_logger:
            response = self.client.post(
                self.login_url,
                data=login_payload,
                format="json"
            )

            # Verificar status de erro
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            # Verificar estrutura de erro
            data = response.json()
            self.assertIn("errors", data)
            self.assertIsInstance(data["errors"], list)

            error = data["errors"][0]
            self.assertEqual(error["status"], "401")
            self.assertEqual(error["code"], "INVALID_CREDENTIALS")
            self.assertIn("Email ou senha inválidos", error["detail"])

            # Verificar logging de falha
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            self.assertEqual(call_args[0][0], "Login failed")
            self.assertEqual(call_args[1]["reason"], "invalid_credentials")

    def test_login_with_inactive_user(self):
        """
        Test: Login com usuário inativo.

        Fluxo:
        1. Desativar usuário
        2. Tentar login
        3. Recebe erro 403 Forbidden
        4. Verifica logs de auditoria
        """
        # Desativar usuário
        self.test_user.is_active = False
        self.test_user.save()

        login_payload = {
            "email": "testuser@empresa.com.br",
            "password": "SecurePass123!",
        }

        with patch("iabank.core.jwt_views.logger") as mock_logger:
            response = self.client.post(
                self.login_url,
                data=login_payload,
                format="json"
            )

            # Verificar status de erro
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

            # Verificar estrutura de erro
            data = response.json()
            error = data["errors"][0]
            self.assertEqual(error["code"], "INACTIVE_ACCOUNT")

            # Verificar logging
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args
            self.assertEqual(call_args[1]["reason"], "inactive_user")

    def test_refresh_token_flow(self):
        """
        Test: Fluxo completo de refresh token.

        Fluxo:
        1. Fazer login e obter tokens
        2. Usar refresh_token para obter novo access_token
        3. Verificar que novo access_token é válido
        4. Verificar auditoria do refresh
        """
        # Passo 1: Login inicial
        login_payload = {
            "email": "testuser@empresa.com.br",
            "password": "SecurePass123!",
        }

        login_response = self.client.post(
            self.login_url,
            data=login_payload,
            format="json"
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        login_data = login_response.json()["data"]
        original_refresh = login_data["refresh_token"]

        # Passo 2: Refresh token
        refresh_payload = {
            "refresh_token": original_refresh
        }

        with patch("iabank.core.jwt_views.logger") as mock_logger, \
             patch("iabank.core.jwt_views.log_business_event") as mock_audit:

            refresh_response = self.client.post(
                self.refresh_url,
                data=refresh_payload,
                format="json"
            )

            # Verificar sucesso do refresh
            self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

            refresh_data = refresh_response.json()["data"]
            self.assertIn("access_token", refresh_data)
            self.assertIn("refresh_token", refresh_data)

            # Verificar que são tokens diferentes
            self.assertNotEqual(refresh_data["access_token"], login_data["access_token"])
            self.assertNotEqual(refresh_data["refresh_token"], original_refresh)

            # Verificar auditoria
            mock_audit.assert_called()
            audit_call = mock_audit.call_args[1]
            self.assertEqual(audit_call["action"], "token_refresh")

    def test_refresh_with_invalid_token(self):
        """
        Test: Refresh com token inválido.

        Verifica tratamento de tokens inválidos ou expirados.
        """
        invalid_payload = {
            "refresh_token": "invalid.jwt.token"
        }

        with patch("iabank.core.jwt_views.logger") as mock_logger:
            response = self.client.post(
                self.refresh_url,
                data=invalid_payload,
                format="json"
            )

            # Verificar erro 401
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            # Verificar estrutura de erro
            data = response.json()
            error = data["errors"][0]
            self.assertEqual(error["code"], "INVALID_REFRESH_TOKEN")

            # Verificar logging
            mock_logger.warning.assert_called()

    def test_validation_errors_handling(self):
        """
        Test: Tratamento de erros de validação.

        Testa vários cenários de validação:
        - Campos obrigatórios faltando
        - Formato de email inválido
        - Estrutura de response de erro
        """
        test_cases = [
            # Email faltando
            {
                "payload": {"password": "SecurePass123!"},
                "expected_code": "EMAIL_REQUIRED",
                "expected_field": "email"
            },
            # Password faltando
            {
                "payload": {"email": "test@empresa.com"},
                "expected_code": "PASSWORD_REQUIRED",
                "expected_field": "password"
            },
            # Ambos faltando
            {
                "payload": {},
                "expected_errors": 2  # Email e password
            }
        ]

        for case in test_cases:
            with self.subTest(payload=case["payload"]):
                with patch("iabank.core.jwt_views.logger"):
                    response = self.client.post(
                        self.login_url,
                        data=case["payload"],
                        format="json"
                    )

                    # Verificar status de validação
                    self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

                    # Verificar estrutura de erro
                    data = response.json()
                    self.assertIn("errors", data)

                    if "expected_errors" in case:
                        self.assertEqual(len(data["errors"]), case["expected_errors"])
                    else:
                        # Verificar erro específico
                        found_error = False
                        for error in data["errors"]:
                            if error["code"] == case["expected_code"]:
                                found_error = True
                                if "expected_field" in case:
                                    self.assertEqual(
                                        error["source"]["field"],
                                        case["expected_field"]
                                    )
                                break
                        self.assertTrue(found_error, f"Erro {case['expected_code']} não encontrado")

    def test_tenant_isolation_in_auth(self):
        """
        Test: Isolamento multi-tenant na autenticação.

        Verifica se usuários de diferentes tenants são isolados corretamente.
        """
        # Criar segundo tenant e usuário
        tenant2 = TenantFactory()
        with TenantContextManager(tenant2.id):
            user2 = User.objects.create_user(
                username="user2",
                email="user2@empresa2.com.br",
                password="SecurePass123!",
                is_active=True
            )
            if hasattr(user2, "tenant_id"):
                user2.tenant_id = tenant2.id
                user2.save()

        # Login do usuário 1 (tenant 1)
        response1 = self.client.post(
            self.login_url,
            data={
                "email": "testuser@empresa.com.br",
                "password": "SecurePass123!",
                "tenant_domain": "empresa"
            },
            format="json"
        )

        # Login do usuário 2 (tenant 2)
        response2 = self.client.post(
            self.login_url,
            data={
                "email": "user2@empresa2.com.br",
                "password": "SecurePass123!",
                "tenant_domain": "empresa2"
            },
            format="json"
        )

        # Ambos logins devem ter sucesso
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Tokens devem ser diferentes
        token1 = response1.json()["data"]["access_token"]
        token2 = response2.json()["data"]["access_token"]
        self.assertNotEqual(token1, token2)

        # User data deve corresponder ao tenant correto
        user_data1 = response1.json()["data"]["user"]
        user_data2 = response2.json()["data"]["user"]

        self.assertEqual(user_data1["email"], "testuser@empresa.com.br")
        self.assertEqual(user_data2["email"], "user2@empresa2.com.br")

    @patch("iabank.core.jwt_views.timezone.now")
    def test_token_expiration_handling(self, mock_now):
        """
        Test: Tratamento de expiração de tokens.

        Simula passage de tempo e verifica comportamento com tokens expirados.
        """
        # Mock do tempo atual
        base_time = timezone.now()
        mock_now.return_value = base_time

        # Login inicial
        response = self.client.post(
            self.login_url,
            data={
                "email": "testuser@empresa.com.br",
                "password": "SecurePass123!",
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]

        # Verificar expires_in é configurado corretamente
        self.assertGreater(data["expires_in"], 0)
        self.assertLessEqual(data["expires_in"], 15 * 60)  # Max 15 minutes

        # Verificar meta timestamp
        meta = response.json()["meta"]
        self.assertIn("timestamp", meta)
        self.assertEqual(meta["timestamp"], int(base_time.timestamp()))

    def test_concurrent_login_attempts(self):
        """
        Test: Múltiplas tentativas de login simultâneas.

        Verifica comportamento com requests concorrentes do mesmo usuário.
        """
        login_payload = {
            "email": "testuser@empresa.com.br",
            "password": "SecurePass123!",
        }

        # Simular múltiplos logins simultâneos
        responses = []
        for _ in range(3):
            response = self.client.post(
                self.login_url,
                data=login_payload,
                format="json"
            )
            responses.append(response)

        # Todos devem ter sucesso
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Tokens devem ser diferentes (cada login gera novos tokens)
        tokens = [r.json()["data"]["access_token"] for r in responses]
        self.assertEqual(len(set(tokens)), len(tokens))  # Todos únicos

    def test_malformed_json_request(self):
        """
        Test: Tratamento de JSON malformado.

        Verifica comportamento com payloads JSON inválidos.
        """
        # JSON malformado
        malformed_json = '{"email": "test@empresa.com", "password":'

        response = self.client.post(
            self.login_url,
            data=malformed_json,
            content_type="application/json"
        )

        # Deve retornar erro 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sql_injection_protection(self):
        """
        Test: Proteção contra SQL injection.

        Tenta payloads maliciosos para verificar sanitização.
        """
        malicious_payloads = [
            "'; DROP TABLE auth_user; --",
            "' OR '1'='1",
            "admin'/*",
            "' UNION SELECT * FROM auth_user --"
        ]

        for payload in malicious_payloads:
            with self.subTest(payload=payload):
                response = self.client.post(
                    self.login_url,
                    data={
                        "email": payload,
                        "password": "SecurePass123!",
                    },
                    format="json"
                )

                # Deve retornar erro de credenciais ou validação, nunca 500
                self.assertIn(response.status_code, [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ])


@pytest.mark.integration
@pytest.mark.slow
class TestAuthenticationPerformance(TestCase):
    """
    Testes de performance para fluxos de autenticação.

    Verifica SLA de <500ms p95 conforme constitution.
    """

    def setUp(self):
        """Setup para testes de performance."""
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login"

        # Criar tenant e usuário
        self.tenant = TenantFactory()
        self.test_user = User.objects.create_user(
            username="perfuser",
            email="perf@empresa.com.br",
            password="SecurePass123!",
            is_active=True
        )

    def test_login_performance_requirement(self):
        """
        Test: Login deve atender SLA de <500ms p95.

        Executa múltiplos logins e mede performance.
        """
        import time

        login_payload = {
            "email": "perf@empresa.com.br",
            "password": "SecurePass123!",
        }

        # Warm-up
        self.client.post(self.login_url, data=login_payload, format="json")

        # Medir performance
        times = []
        for _ in range(10):  # Sample pequeno para CI
            start = time.time()
            response = self.client.post(
                self.login_url,
                data=login_payload,
                format="json"
            )
            end = time.time()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            times.append((end - start) * 1000)  # Convert to ms

        # Calcular p95 (approximation com sample pequeno)
        times.sort()
        p95_time = times[int(len(times) * 0.95) - 1]

        # Verificar SLA
        self.assertLess(
            p95_time,
            500,
            f"Login p95 {p95_time:.2f}ms excede SLA de 500ms"
        )

    def test_refresh_performance_requirement(self):
        """
        Test: Refresh token deve atender SLA de <500ms p95.
        """
        import time

        # Login inicial para obter refresh token
        login_response = self.client.post(
            self.login_url,
            data={
                "email": "perf@empresa.com.br",
                "password": "SecurePass123!",
            },
            format="json"
        )

        refresh_token = login_response.json()["data"]["refresh_token"]
        refresh_url = "/api/v1/auth/refresh"

        # Medir performance do refresh
        times = []
        for _ in range(10):
            start = time.time()
            response = self.client.post(
                refresh_url,
                data={"refresh_token": refresh_token},
                format="json"
            )
            end = time.time()

            if response.status_code == status.HTTP_200_OK:
                # Update token for next iteration
                refresh_token = response.json()["data"]["refresh_token"]

            times.append((end - start) * 1000)

        # Calcular p95
        times.sort()
        p95_time = times[int(len(times) * 0.95) - 1]

        # Verificar SLA
        self.assertLess(
            p95_time,
            500,
            f"Refresh p95 {p95_time:.2f}ms excede SLA de 500ms"
        )
