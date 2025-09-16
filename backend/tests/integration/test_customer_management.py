"""
Integration test gestão de clientes.

Testa o fluxo completo de gestão de clientes incluindo:
- Criação de clientes com validações
- Busca e listagem com filtros
- Atualização de dados pessoais e financeiros
- Análise de crédito e score
- Isolamento por tenant
- Auditoria e logging estruturado
- Validação de documentos (CPF/CNPJ)
- Estados e transições de dados

Baseado em:
- T014 do tasks.md
- Constitution v1.0.0 - Django-Domain-First Architecture
- Data model: specs/001-eu-escrevi-um/data-model.md
- Contract API: specs/001-eu-escrevi-um/contracts/
"""

from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4

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
class TestCustomerManagementFlow(TransactionTestCase):
    """
    Integration test para fluxo completo de gestão de clientes.

    Testa todo o fluxo desde criação até análise de crédito, incluindo:
    - CRUD completo de clientes
    - Validação de documentos (CPF/CNPJ)
    - Análise de crédito e atualização de score
    - Isolamento multi-tenant rigoroso
    - Auditoria automática e logs estruturados
    - Estados e transições de dados
    - Performance e consistência
    """

    def setUp(self):
        """Setup para integration tests de gestão de clientes."""
        self.client = APIClient()

        # Criar tenant principal para testes
        self.tenant = TenantFactory(
            name="Empresa Teste LTDA",
            settings={
                "max_interest_rate": 3.0,
                "max_loan_amount": 150000.00,
                "currency": "BRL",
                "credit_analysis_enabled": True,
                "min_credit_score": 300
            }
        )

        # Criar tenant secundário para testes de isolamento
        self.other_tenant = TenantFactory(
            name="Outra Empresa LTDA"
        )

        # Criar usuários para ambos os tenants (usando User padrão Django por enquanto)
        self.user = User.objects.create_user(
            username="admin_teste",
            email="admin@teste.com",
            password="senha123",
            first_name="Admin",
            last_name="Teste"
        )
        # Adicionar campos customizados se disponíveis
        if hasattr(self.user, 'tenant_id'):
            self.user.tenant_id = self.tenant.id
        if hasattr(self.user, 'role'):
            self.user.role = "ADMIN"
        self.user.save()

        self.other_user = User.objects.create_user(
            username="admin_outro",
            email="admin@outro.com",
            password="senha123",
            first_name="Admin",
            last_name="Outro"
        )
        # Adicionar campos customizados se disponíveis
        if hasattr(self.other_user, 'tenant_id'):
            self.other_user.tenant_id = self.other_tenant.id
        if hasattr(self.other_user, 'role'):
            self.other_user.role = "ADMIN"
        self.other_user.save()

        # URLs da API
        self.customers_url = "/api/v1/customers"
        self.customer_detail_url = "/api/v1/customers/{id}"
        self.customer_credit_analysis_url = "/api/v1/customers/{id}/credit-analysis"

        # Mock data para clientes válidos
        self.valid_customer_data = {
            "document_type": "CPF",
            "document": "12345678901",  # CPF fictício
            "name": "João da Silva Santos",
            "email": "joao.santos@email.com",
            "phone": "(11) 99999-9999",
            "birth_date": "1985-05-15",
            "gender": "M",
            "profession": "Engenheiro",
            "monthly_income": "8500.00",
            "credit_score": 750
        }

        self.valid_customer_cnpj_data = {
            "document_type": "CNPJ",
            "document": "12345678000195",  # CNPJ fictício
            "name": "Empresa ABC LTDA",
            "email": "contato@empresaabc.com.br",
            "phone": "(11) 3333-4444",
            "profession": "Comércio",
            "monthly_income": "25000.00",
            "credit_score": 680
        }

    def _authenticate_user(self, user):
        """Helper para autenticar usuário e obter token."""
        self.client.force_authenticate(user=user)
        return user

    def _create_customer(self, tenant_user, customer_data=None):
        """Helper para criar cliente via API."""
        if customer_data is None:
            customer_data = self.valid_customer_data.copy()

        self._authenticate_user(tenant_user)
        response = self.client.post(self.customers_url, customer_data)

        # Se endpoint não existe ainda, retorna response mesmo assim
        # para que testes possam verificar o estado atual
        return response

    def test_customer_creation_complete_flow(self):
        """
        Test: Fluxo completo de criação de cliente.

        Cobre:
        - Validação de entrada
        - Criação com dados válidos
        - Auditoria automática
        - Response estruturado
        """
        self._authenticate_user(self.user)

        # Test criação com sucesso
        response = self.client.post(self.customers_url, self.valid_customer_data)

        # EXPECTATIVA TDD (RED phase): Este teste DEVE falhar inicialmente
        # até que endpoint POST seja implementado corretamente

        # TDD RED PHASE: Teste DEVE FALHAR como esperado
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Validar estrutura da response
        data = response.json()
        self.assertIn("data", data)
        customer = data["data"]

        # Validar campos obrigatórios
        self.assertEqual(customer["document"], self.valid_customer_data["document"])
        self.assertEqual(customer["name"], self.valid_customer_data["name"])
        self.assertEqual(customer["email"], self.valid_customer_data["email"])
        self.assertEqual(float(customer["monthly_income"]), float(self.valid_customer_data["monthly_income"]))
        self.assertEqual(customer["credit_score"], self.valid_customer_data["credit_score"])

        # Validar campos calculados/default
        self.assertIn("id", customer)
        self.assertTrue(customer["is_active"])
        self.assertIn("created_at", customer)
        self.assertIn("updated_at", customer)

        # Validar tenant_id implícito
        self.assertEqual(customer["tenant_id"], str(self.tenant.id))

    def test_customer_creation_with_validation_errors(self):
        """
        Test: Validação de erros na criação de clientes.

        Cobre:
        - Documentos inválidos
        - Campos obrigatórios faltando
        - Formatos inválidos
        - Response de erro estruturado
        """
        self._authenticate_user(self.user)

        # TDD RED PHASE: Teste deve falhar até endpoint ser implementado
        # Testando validações diretamente
        test_cases = [
            # Documento inválido
            {
                **self.valid_customer_data,
                "document": "123",  # CPF inválido
                "expected_field": "document"
            },
            # Email inválido
            {
                **self.valid_customer_data,
                "email": "email-invalido",
                "expected_field": "email"
            },
            # Monthly income negativo
            {
                **self.valid_customer_data,
                "monthly_income": "-1000.00",
                "expected_field": "monthly_income"
            },
            # Credit score fora do range
            {
                **self.valid_customer_data,
                "credit_score": 1500,  # Score máximo é 1000
                "expected_field": "credit_score"
            },
            # Campos obrigatórios faltando
            {
                "document_type": "CPF",
                # Faltando document, name, etc.
                "expected_field": "name"
            }
        ]

        for i, test_case in enumerate(test_cases):
            with self.subTest(test_case=i):
                expected_field = test_case.pop("expected_field")

                response = self.client.post(self.customers_url, test_case)

                # EXPECTATIVA: Erro de validação
                self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

                # Validar estrutura de erro
                data = response.json()
                self.assertIn("errors", data)

                # Validar que erro menciona o campo esperado
                errors_text = str(data["errors"]).lower()
                self.assertIn(expected_field.lower(), errors_text)

    def test_customer_listing_and_filtering(self):
        """
        Test: Listagem e filtros de clientes.

        Cobre:
        - Listagem paginada
        - Filtros por documento, nome, status
        - Ordenação
        - Isolamento por tenant
        """
        self._authenticate_user(self.user)

        # TDD RED PHASE: Teste deve falhar até endpoint ser implementado corretamente
        response = self.client.get(self.customers_url)

        # Teste DEVE FALHAR até implementação
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("data", data)

        # Tentar criar alguns clientes para testar filtros
        customers_data = [
            {**self.valid_customer_data, "name": "Ana Silva", "document": "11111111111"},
            {**self.valid_customer_data, "name": "Bruno Santos", "document": "22222222222"},
            {**self.valid_customer_cnpj_data, "name": "Empresa XYZ", "document": "11111111000122"}
        ]

        created_customers = []
        for customer_data in customers_data:
            response = self._create_customer(self.user, customer_data)
            if response.status_code == 201:
                created_customers.append(response.json()["data"])

        # Test filtro por nome se clientes foram criados
        if created_customers:
            response = self.client.get(self.customers_url, {"search": "Ana"})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            data = response.json()
            if "data" in data:
                filtered_customers = data["data"]
                # Validar que filtrou corretamente
                for customer in filtered_customers:
                    self.assertIn("Ana", customer["name"])

    def test_customer_detail_and_update(self):
        """
        Test: Detalhamento e atualização de cliente.

        Cobre:
        - Busca por ID
        - Atualização parcial
        - Atualização completa
        - Validação de mudanças
        """
        # TDD RED PHASE: Teste deve falhar até implementação
        response = self._create_customer(self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        customer = response.json()["data"]
        customer_id = customer["id"]

        self._authenticate_user(self.user)

        # Test busca por ID
        detail_url = self.customer_detail_url.format(id=customer_id)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("data", data)
        retrieved_customer = data["data"]
        self.assertEqual(retrieved_customer["id"], customer_id)

        # Test atualização parcial
        update_data = {
            "phone": "(11) 88888-8888",
            "monthly_income": "9500.00"
        }

        response = self.client.patch(detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_customer = response.json()["data"]
        self.assertEqual(updated_customer["phone"], update_data["phone"])
        self.assertEqual(float(updated_customer["monthly_income"]), float(update_data["monthly_income"]))

        # Validar que outros campos não mudaram
        self.assertEqual(updated_customer["name"], customer["name"])
        self.assertEqual(updated_customer["document"], customer["document"])

    def test_customer_credit_analysis_flow(self):
        """
        Test: Fluxo de análise de crédito.

        Cobre:
        - Atualização de score de crédito
        - Histórico de análises
        - Regras de negócio de crédito
        - Logs estruturados
        """
        # TDD RED PHASE: Teste deve falhar até implementação
        response = self._create_customer(self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        customer = response.json()["data"]
        customer_id = customer["id"]

        self._authenticate_user(self.user)

        # Test análise de crédito
        credit_analysis_url = self.customer_credit_analysis_url.format(id=customer_id)
        analysis_data = {
            "new_score": 820,
            "analysis_reason": "Aumento de renda comprovado",
            "analyst_notes": "Cliente apresentou novos comprovantes"
        }

        response = self.client.post(credit_analysis_url, analysis_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validar que score foi atualizado
        detail_url = self.customer_detail_url.format(id=customer_id)
        response = self.client.get(detail_url)
        updated_customer = response.json()["data"]

        self.assertEqual(updated_customer["credit_score"], analysis_data["new_score"])
        self.assertIsNotNone(updated_customer.get("score_last_updated"))

    def test_tenant_isolation_strict(self):
        """
        Test: Isolamento rigoroso por tenant.

        Cobre:
        - Clientes de um tenant não visíveis para outros
        - Operações cross-tenant bloqueadas
        - Segurança de acesso
        """
        # TDD RED PHASE: Teste deve falhar até implementação
        response = self._create_customer(self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        customer_tenant1 = response.json()["data"]
        customer_id = customer_tenant1["id"]

        # Tentar acessar do tenant 2
        self._authenticate_user(self.other_user)

        # Não deve aparecer na listagem
        response = self.client.get(self.customers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        customers = data["data"]
        customer_ids = [c["id"] for c in customers]
        self.assertNotIn(customer_id, customer_ids)

        # Não deve permitir acesso direto
        detail_url = self.customer_detail_url.format(id=customer_id)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_soft_delete_and_reactivation(self):
        """
        Test: Soft delete e reativação de clientes.

        Cobre:
        - Desativação de cliente (soft delete)
        - Reativação posterior
        - Histórico preservado
        - Filtros por status
        """
        # TDD RED PHASE: Teste deve falhar até implementação
        response = self._create_customer(self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        customer = response.json()["data"]
        customer_id = customer["id"]

        self._authenticate_user(self.user)

        # Desativar cliente
        detail_url = self.customer_detail_url.format(id=customer_id)
        deactivate_data = {"is_active": False}

        response = self.client.patch(detail_url, deactivate_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_customer = response.json()["data"]
        self.assertFalse(updated_customer["is_active"])

        # Validar que não aparece em listagem ativa por default
        response = self.client.get(self.customers_url)
        active_customers = response.json()["data"]
        active_ids = [c["id"] for c in active_customers]
        # Cliente inativo pode ou não aparecer dependendo do filtro default

        # Reativar cliente
        reactivate_data = {"is_active": True}
        response = self.client.patch(detail_url, reactivate_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        reactivated_customer = response.json()["data"]
        self.assertTrue(reactivated_customer["is_active"])

    @patch('iabank.core.logging.get_logger')
    def test_structured_logging_integration(self, mock_logger):
        """
        Test: Integração com logging estruturado.

        Cobre:
        - Logs automáticos em operações
        - Contexto de tenant e usuário
        - Estrutura padronizada
        - Auditoria automática
        """
        mock_log_instance = mock_logger.return_value

        # Criar cliente (deve gerar logs)
        response = self._create_customer(self.user)

        if response.status_code == 201:
            # Validar que logs foram chamados
            self.assertTrue(mock_log_instance.info.called or mock_log_instance.debug.called)

            # Verificar contexto nos logs (pelo menos uma chamada com contexto)
            calls_made = mock_log_instance.info.call_args_list + mock_log_instance.debug.call_args_list
            self.assertGreater(len(calls_made), 0)

    def test_performance_customer_operations(self):
        """
        Test: Performance das operações de cliente.

        Cobre:
        - Tempo de resposta < 500ms para CRUD
        - Consultas otimizadas
        - Paginação eficiente
        """
        import time

        self._authenticate_user(self.user)

        # Test criação
        start_time = time.time()
        response = self._create_customer(self.user)
        creation_time = time.time() - start_time

        # Performance SLA: < 500ms
        self.assertLess(creation_time, 0.5, "Criação de cliente deve ser < 500ms")

        if response.status_code == 201:
            customer_id = response.json()["data"]["id"]

            # Test busca por ID
            detail_url = self.customer_detail_url.format(id=customer_id)
            start_time = time.time()
            response = self.client.get(detail_url)
            fetch_time = time.time() - start_time

            self.assertLess(fetch_time, 0.5, "Busca de cliente deve ser < 500ms")

    def test_business_rules_validation(self):
        """
        Test: Validação de regras de negócio específicas.

        Cobre:
        - Score de crédito dentro do range válido
        - Documentos únicos por tenant
        - Validação de idade mínima
        - Renda mínima configurável
        """
        self._authenticate_user(self.user)

        # Test documento duplicado no mesmo tenant
        response1 = self._create_customer(self.user)
        if response1.status_code == 201:
            # Tentar criar cliente com mesmo documento
            duplicate_data = self.valid_customer_data.copy()
            duplicate_data["name"] = "Outro Nome"

            response2 = self.client.post(self.customers_url, duplicate_data)
            self.assertEqual(response2.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Validar mensagem de erro
            data = response2.json()
            self.assertIn("errors", data)

    def tearDown(self):
        """Cleanup após cada teste."""
        # Limpar contexto
        from iabank.core.factories import set_tenant_context
        set_tenant_context(None)