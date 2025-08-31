"""
Views do app Finance.

Implementa os endpoints da API REST para gestão financeira,
incluindo contas, categorias, fornecedores e transações.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import BankAccount, PaymentCategory, CostCenter, Supplier, FinancialTransaction
from .serializers import (
    BankAccountSerializer,
    PaymentCategorySerializer,
    CostCenterSerializer,
    SupplierSerializer,
    FinancialTransactionListSerializer,
    FinancialTransactionDetailSerializer,
    FinancialTransactionCreateSerializer
)


class BankAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de contas bancárias.
    
    Permite gestão completa de contas bancárias com
    cálculo automático de saldos atuais.
    """
    
    serializer_class = BankAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'bank_name', 'account_number']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtra contas bancárias pelo tenant atual."""
        return BankAccount.objects.filter(tenant=self.request.tenant)
    
    def perform_create(self, serializer):
        """Associa a conta ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)


class PaymentCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para operações CRUD de categorias de pagamento."""
    
    serializer_class = PaymentCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtra categorias pelo tenant atual."""
        return PaymentCategory.objects.filter(tenant=self.request.tenant)
    
    def perform_create(self, serializer):
        """Associa a categoria ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)


class CostCenterViewSet(viewsets.ModelViewSet):
    """ViewSet para operações CRUD de centros de custo."""
    
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering = ['code']
    
    def get_queryset(self):
        """Filtra centros de custo pelo tenant atual."""
        return CostCenter.objects.filter(tenant=self.request.tenant)
    
    def perform_create(self, serializer):
        """Associa o centro de custo ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet para operações CRUD de fornecedores."""
    
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'document_number', 'email']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtra fornecedores pelo tenant atual."""
        return Supplier.objects.filter(tenant=self.request.tenant)
    
    def perform_create(self, serializer):
        """Associa o fornecedor ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)


class FinancialTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de transações financeiras.
    
    Inclui funcionalidades especiais como filtros por período,
    relatórios de fluxo de caixa e marcação de pagamentos.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'type', 'is_paid', 'bank_account', 'category', 
        'cost_center', 'supplier'
    ]
    search_fields = ['description', 'supplier__name', 'category__name']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        """Filtra transações pelo tenant atual."""
        return FinancialTransaction.objects.filter(
            tenant=self.request.tenant
        ).select_related('bank_account', 'category', 'supplier', 'cost_center')
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action."""
        if self.action == 'list':
            return FinancialTransactionListSerializer
        elif self.action == 'create':
            return FinancialTransactionCreateSerializer
        else:
            return FinancialTransactionDetailSerializer
    
    def perform_create(self, serializer):
        """Associa a transação ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Marca uma transação como paga."""
        transaction = self.get_object()
        
        payment_date = request.data.get('payment_date')
        if not payment_date:
            payment_date = timezone.now().date()
        
        transaction.is_paid = True
        transaction.payment_date = payment_date
        transaction.save()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)
    
    @action(detail=False)
    def overdue(self, request):
        """Endpoint para listar transações vencidas."""
        overdue_transactions = self.get_queryset().filter(
            due_date__lt=timezone.now().date(),
            is_paid=False
        )
        
        serializer = FinancialTransactionListSerializer(overdue_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def cash_flow(self, request):
        """Endpoint para relatório de fluxo de caixa."""
        from django.db.models import Sum, Case, When, DecimalField
        from datetime import datetime, timedelta
        
        # Parâmetros de período
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Padrão: últimos 30 dias
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        transactions = self.get_queryset().filter(
            transaction_date__range=[start_date, end_date]
        )
        
        summary = transactions.aggregate(
            total_income=Sum(
                Case(
                    When(type=FinancialTransaction.TransactionType.INCOME, then='amount'),
                    default=0,
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
            total_expense=Sum(
                Case(
                    When(type=FinancialTransaction.TransactionType.EXPENSE, then='amount'),
                    default=0,
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            )
        )
        
        summary['total_income'] = summary['total_income'] or 0
        summary['total_expense'] = summary['total_expense'] or 0
        summary['net_flow'] = summary['total_income'] - summary['total_expense']
        summary['period'] = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        return Response(summary)