"""
Endpoints para setup de dados de teste E2E.
ATENÇÃO: Apenas para ambiente de desenvolvimento!
"""
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.db import transaction
import json

from iabank.core.models import Tenant
from iabank.customers.models import Customer, Address
from iabank.operations.models import Loan, Installment
from iabank.finance.models import BankAccount, FinancialTransaction, PaymentCategory

logger = logging.getLogger(__name__)
User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def setup_test_data(request):
    """
    Setup de dados de teste para E2E.
    Cria tenant, usuário, cliente e dados básicos.
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Endpoint disponível apenas em DEBUG"}, status=403)

    try:
        data = json.loads(request.body)
        tenant_name = data.get('tenant', 'test-tenant')
        user_data = data.get('user', {})
        customer_data = data.get('customer', {})

        with transaction.atomic():
            # Criar ou obter tenant
            tenant, created = Tenant.objects.get_or_create(
                name=tenant_name,
                defaults={
                    'slug': tenant_name,
                    'domain': f'{tenant_name}.localhost',
                    'is_active': True
                }
            )

            # Criar usuário de teste
            user, created = User.objects.get_or_create(
                email=user_data.get('email', 'test@test.com'),
                tenant=tenant,
                defaults={
                    'first_name': 'Test',
                    'last_name': 'User',
                    'is_active': True,
                    'role': user_data.get('role', 'admin')
                }
            )
            if created:
                user.set_password(user_data.get('password', 'test123'))
                user.save()

            # Criar cliente de teste
            customer, created = Customer.objects.get_or_create(
                document_number=customer_data.get('document_number', '12345678901'),
                tenant=tenant,
                defaults={
                    'name': customer_data.get('name', 'João Silva'),
                    'email': customer_data.get('email', 'joao@test.com'),
                    'phone': '11999999999',
                    'monthly_income': 5000.00,
                    'credit_score': 750,
                    'risk_level': 'low'
                }
            )

            # Criar endereço para o cliente
            if created:
                Address.objects.create(
                    customer=customer,
                    street='Rua Teste, 123',
                    city='São Paulo',
                    state='SP',
                    postal_code='01234567',
                    is_primary=True,
                    tenant=tenant
                )

            # Criar conta bancária de teste
            bank_account, _ = BankAccount.objects.get_or_create(
                bank_name='Banco Teste',
                tenant=tenant,
                defaults={
                    'account_number': '12345',
                    'agency': '0001',
                    'account_type': 'checking',
                    'balance': 100000.00,
                    'is_active': True
                }
            )

            logger.info(f"Test data setup completed for tenant: {tenant_name}")

            return JsonResponse({
                "status": "success",
                "data": {
                    "tenant_id": str(tenant.id),
                    "user_id": user.id,
                    "customer_id": customer.id,
                    "bank_account_id": bank_account.id
                }
            })

    except Exception as e:
        logger.error(f"Error setting up test data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def setup_financial_data(request):
    """
    Setup de dados financeiros para testes de relatório.
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Endpoint disponível apenas em DEBUG"}, status=403)

    try:
        data = json.loads(request.body)
        tenant_name = data.get('tenant', 'test-tenant')

        with transaction.atomic():
            tenant = Tenant.objects.get(name=tenant_name)

            # Criar categorias de pagamento
            categories = [
                {'name': 'Receita Empréstimos', 'type': 'income'},
                {'name': 'Despesas Operacionais', 'type': 'expense'},
                {'name': 'Comissões', 'type': 'expense'}
            ]

            for cat_data in categories:
                PaymentCategory.objects.get_or_create(
                    name=cat_data['name'],
                    tenant=tenant,
                    defaults={
                        'type': cat_data['type'],
                        'is_active': True
                    }
                )

            # Criar transações financeiras de exemplo
            bank_account = BankAccount.objects.filter(tenant=tenant).first()
            income_category = PaymentCategory.objects.filter(tenant=tenant, type='income').first()
            expense_category = PaymentCategory.objects.filter(tenant=tenant, type='expense').first()

            if bank_account and income_category:
                # Receitas
                FinancialTransaction.objects.get_or_create(
                    description='Pagamento Empréstimo - João Silva',
                    tenant=tenant,
                    defaults={
                        'amount': 1500.00,
                        'type': 'income',
                        'category': income_category,
                        'bank_account': bank_account,
                        'status': 'completed'
                    }
                )

                # Despesas
                if expense_category:
                    FinancialTransaction.objects.get_or_create(
                        description='Despesa Administrativa',
                        tenant=tenant,
                        defaults={
                            'amount': 500.00,
                            'type': 'expense',
                            'category': expense_category,
                            'bank_account': bank_account,
                            'status': 'completed'
                        }
                    )

            logger.info(f"Financial test data setup completed for tenant: {tenant_name}")

            return JsonResponse({
                "status": "success",
                "message": "Financial data created successfully"
            })

    except Exception as e:
        logger.error(f"Error setting up financial test data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_overdue_loan(request):
    """
    Criar empréstimo em atraso para testes.
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Endpoint disponível apenas em DEBUG"}, status=403)

    try:
        data = json.loads(request.body)

        with transaction.atomic():
            # Buscar cliente e dados necessários
            customer_id = data.get('customer_id', 1)
            customer = Customer.objects.get(id=customer_id)

            # Criar empréstimo
            loan = Loan.objects.create(
                customer=customer,
                principal_amount=data.get('amount', 10000.00),
                installments_count=data.get('installments', 12),
                interest_rate=0.025,  # 2.5% a.m.
                status='active',
                tenant=customer.tenant
            )

            # Criar parcelas (simulando atraso)
            overdue_days = data.get('overdue_days', 5)
            from datetime import datetime, timedelta

            for i in range(loan.installments_count):
                due_date = datetime.now().date() - timedelta(days=overdue_days if i == 0 else -30*i)
                status = 'overdue' if i == 0 else 'pending'

                Installment.objects.create(
                    loan=loan,
                    installment_number=i + 1,
                    amount=loan.principal_amount / loan.installments_count,
                    due_date=due_date,
                    status=status,
                    tenant=customer.tenant
                )

            logger.info(f"Overdue loan created: {loan.id}")

            return JsonResponse({
                "status": "success",
                "loan_id": loan.id
            })

    except Exception as e:
        logger.error(f"Error creating overdue loan: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def cleanup_test_data(request):
    """
    Limpar dados de teste.
    """
    if not settings.DEBUG:
        return JsonResponse({"error": "Endpoint disponível apenas em DEBUG"}, status=403)

    try:
        tenant_name = request.GET.get('tenant', 'test-tenant')

        with transaction.atomic():
            try:
                tenant = Tenant.objects.get(name=tenant_name)

                # Deletar em ordem para respeitar constraints
                FinancialTransaction.objects.filter(tenant=tenant).delete()
                Installment.objects.filter(tenant=tenant).delete()
                Loan.objects.filter(tenant=tenant).delete()
                Address.objects.filter(tenant=tenant).delete()
                Customer.objects.filter(tenant=tenant).delete()
                BankAccount.objects.filter(tenant=tenant).delete()
                PaymentCategory.objects.filter(tenant=tenant).delete()
                User.objects.filter(tenant=tenant).delete()
                tenant.delete()

                logger.info(f"Test data cleaned up for tenant: {tenant_name}")

            except Tenant.DoesNotExist:
                pass  # Tenant já não existe

        return JsonResponse({"status": "success", "message": "Test data cleaned up"})

    except Exception as e:
        logger.error(f"Error cleaning up test data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)