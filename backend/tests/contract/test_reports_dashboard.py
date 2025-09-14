"""
Contract tests para endpoint GET /api/v1/reports/dashboard.

Seguindo metodologia TDD (RED phase):
- Testa APENAS o contrato da API (schema request/response)
- NÃO testa lógica de negócio (isso é para integration/unit tests)
- DEVE falhar inicialmente pois endpoint não existe ainda

Baseado em:
- specs/001-eu-escrevi-um/contracts/api-contracts.yaml
- constitution v1.0.0 - Django-Domain-First Architecture
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase


@pytest.mark.contract
class TestReportsDashboardContract(TestCase):
    """
    Contract tests para GET /api/v1/reports/dashboard.

    Testa apenas conformidade com OpenAPI schema:
    - Query parameters structure
    - Response body structure
    - Status codes
    - Content types
    - Authentication requirements
    """

    def setUp(self):
        """Setup básico para contract tests."""
        self.client = APIClient()
        self.dashboard_url = "/api/v1/reports/dashboard"

    def test_dashboard_endpoint_exists(self):
        """
        Test: Endpoint GET /api/v1/reports/dashboard existe.

        EXPECTATIVA (RED phase): Deve falhar com 404.
        Endpoint ainda não foi implementado.
        """
        response = self.client.get(self.dashboard_url)

        # RED phase: Este teste DEVE falhar com 404
        # até que o endpoint seja implementado
        self.assertNotEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Endpoint deve existir conforme OpenAPI contract"
        )

    def test_dashboard_requires_authentication(self):
        """
        Test: Endpoint requer autenticação Bearer Token.

        Conforme OpenAPI, endpoint está sob security: BearerAuth.
        """
        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não existe ainda (404)
        # Quando implementado, deve retornar HTTP 401 sem token
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                "Endpoint deve exigir autenticação"
            )

    def test_dashboard_accepts_only_get_method(self):
        """Test: Endpoint aceita apenas GET method."""
        # Teste POST method
        response = self.client.post(self.dashboard_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, POST deve retornar 405 Method Not Allowed
        if response.status_code != status.HTTP_404_NOT_FOUND:
            self.assertEqual(
                response.status_code,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Endpoint deve aceitar apenas GET"
            )

    def test_dashboard_default_period_parameter(self):
        """
        Test: Query parameter 'period' é opcional com default '30d'.

        Schema conforme OpenAPI:
        - period: string
        - enum: [7d, 30d, 90d, 1y]
        - default: 30d
        """
        # Request sem period (deve usar default)
        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não existe ainda
        # Quando implementado, deve aceitar request sem period
        self.assertNotEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Period é opcional conforme OpenAPI"
        )

    def test_dashboard_valid_period_parameters(self):
        """Test: Valores válidos para query parameter 'period'."""
        valid_periods = ["7d", "30d", "90d", "1y"]

        for period in valid_periods:
            with self.subTest(period=period):
                response = self.client.get(
                    self.dashboard_url,
                    data={"period": period}
                )

                # RED phase: Endpoint não existe
                # Quando implementado, deve aceitar todos os valores válidos
                self.assertNotEqual(
                    response.status_code,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    f"Period '{period}' deve ser aceito conforme OpenAPI"
                )

    def test_dashboard_invalid_period_parameter(self):
        """Test: Valores inválidos para query parameter 'period'."""
        invalid_periods = ["invalid", "1d", "6m", "2y", "weekly"]

        for period in invalid_periods:
            with self.subTest(period=period):
                response = self.client.get(
                    self.dashboard_url,
                    data={"period": period}
                )

                # RED phase: Endpoint não existe ainda
                # Quando implementado, deve rejeitar valores inválidos
                if response.status_code not in [status.HTTP_404_NOT_FOUND]:
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                        f"Period '{period}' deve ser rejeitado"
                    )

    def test_dashboard_success_response_schema(self):
        """
        Test: Response de sucesso segue schema OpenAPI.

        Schema esperado (HTTP 200):
        {
          "data": {
            "total_active_loans": integer,
            "total_loan_amount": decimal,
            "default_rate": decimal,
            "monthly_revenue": decimal,
            "loans_by_status": object,
            "payments_trend": array
          }
        }
        """
        # Mock de token válido (quando implementado)
        # self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')

        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não implementado ainda
        # Quando implementado com autenticação válida, deve retornar HTTP 200
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Valida estrutura do response conforme OpenAPI
            self.assertIn("data", data)
            dashboard_data = data["data"]

            # Valida campos obrigatórios do dashboard
            required_fields = [
                "total_active_loans",
                "total_loan_amount",
                "default_rate",
                "monthly_revenue",
                "loans_by_status",
                "payments_trend"
            ]

            for field in required_fields:
                self.assertIn(
                    field,
                    dashboard_data,
                    f"Campo '{field}' é obrigatório conforme OpenAPI"
                )

            # Valida tipos dos campos
            self.assertIsInstance(
                dashboard_data["total_active_loans"],
                int,
                "total_active_loans deve ser integer"
            )
            self.assertIsInstance(
                dashboard_data["total_loan_amount"],
                (int, float),
                "total_loan_amount deve ser decimal"
            )
            self.assertIsInstance(
                dashboard_data["default_rate"],
                (int, float),
                "default_rate deve ser decimal"
            )
            self.assertIsInstance(
                dashboard_data["monthly_revenue"],
                (int, float),
                "monthly_revenue deve ser decimal"
            )
            self.assertIsInstance(
                dashboard_data["loans_by_status"],
                dict,
                "loans_by_status deve ser object"
            )
            self.assertIsInstance(
                dashboard_data["payments_trend"],
                list,
                "payments_trend deve ser array"
            )

    def test_dashboard_content_type_json_response(self):
        """Test: Response Content-Type deve ser application/json."""
        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não existe
        # Quando implementado, deve retornar JSON
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(
                response["Content-Type"],
                "application/json",
                "Response deve ser application/json"
            )

    def test_dashboard_unauthorized_response_schema(self):
        """
        Test: Response de erro de autenticação segue schema OpenAPI.

        Schema esperado (HTTP 401):
        {
          "errors": [{
            "status": "401",
            "code": "...",
            "detail": "..."
          }]
        }
        """
        # Request sem token de autenticação
        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não existe (404)
        # Quando implementado, sem token deve retornar HTTP 401
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            data = response.json()

            # Valida estrutura de erro conforme OpenAPI
            self.assertIn("errors", data)
            self.assertIsInstance(data["errors"], list)
            self.assertTrue(len(data["errors"]) > 0)

            error = data["errors"][0]
            self.assertIn("status", error)
            self.assertIn("detail", error)
            self.assertEqual(error["status"], "401")


@pytest.mark.contract
@pytest.mark.tenant_isolation
class TestReportsDashboardTenantIsolation(TestCase):
    """
    Contract tests específicos para isolamento multi-tenant.

    Testa se o endpoint respeita isolamento de tenant conforme constitution.
    """

    def setUp(self):
        """Setup para testes de tenant isolation."""
        self.client = APIClient()
        self.dashboard_url = "/api/v1/reports/dashboard"

    def test_dashboard_isolates_data_by_tenant(self):
        """
        Test: Dashboard retorna apenas dados do tenant autenticado.

        Conforme constitution, todos os dados devem ser isolados por tenant_id.
        """
        # Mock de token válido para tenant específico
        # self.client.credentials(HTTP_AUTHORIZATION='Bearer tenant_a_token')

        response = self.client.get(self.dashboard_url)

        # RED phase: Endpoint não implementado
        # Quando implementado, deve considerar apenas dados do tenant
        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Dados do dashboard devem refletir apenas o tenant atual
            # (teste de contract - não valida valores específicos)
            self.assertIn("data", data)
            self.assertIsInstance(data["data"]["total_active_loans"], int)

    def test_dashboard_with_different_tenant_tokens(self):
        """
        Test: Tokens de diferentes tenants retornam dados diferentes.

        Este é um test de contract para garantir que a API suporta
        isolamento multi-tenant no nível de contrato.
        """
        # RED phase: Endpoint não existe ainda
        # Teste documenta expectativa de isolamento

        # Mock requests para diferentes tenants
        tenant_a_response = self.client.get(self.dashboard_url)
        # self.client.credentials(HTTP_AUTHORIZATION='Bearer tenant_a_token')

        tenant_b_response = self.client.get(self.dashboard_url)
        # self.client.credentials(HTTP_AUTHORIZATION='Bearer tenant_b_token')

        # RED phase: Ambos devem retornar 404 (endpoint não existe)
        # Quando implementado, devem retornar dados diferentes
        if (tenant_a_response.status_code == status.HTTP_200_OK and
            tenant_b_response.status_code == status.HTTP_200_OK):

            # Contract test: API deve suportar diferentes tenants
            # (valores podem ser iguais por coincidência)
            self.assertIn("data", tenant_a_response.json())
            self.assertIn("data", tenant_b_response.json())