"""
Views do app Operations.

Implementa os endpoints da API REST para gestão de empréstimos,
consultores e parcelas, com lógica de negócio integrada.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Consultant, Loan, Installment
from .serializers import (
    ConsultantSerializer,
    LoanListSerializer,
    LoanDetailSerializer,
    LoanCreateSerializer,
    InstallmentSerializer
)


class ConsultantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para operações de leitura de consultores.
    
    Fornece endpoints para listar e visualizar consultores,
    com filtros para seleção em formulários.
    """
    
    serializer_class = ConsultantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['user__first_name', 'user__last_name']
    
    def get_queryset(self):
        """Filtra consultores pelo tenant atual."""
        return Consultant.objects.filter(
            tenant=self.request.tenant
        ).select_related('user')


class LoanViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD completas de empréstimos.
    
    Inclui funcionalidades especiais como geração automática
    de parcelas e operações de pagamento.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'consultant', 'customer']
    search_fields = ['customer__name', 'customer__document_number']
    ordering_fields = ['contract_date', 'created_at', 'principal_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtra empréstimos pelo tenant atual."""
        return Loan.objects.filter(
            tenant=self.request.tenant
        ).select_related('customer', 'consultant__user')
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action."""
        if self.action == 'list':
            return LoanListSerializer
        elif self.action == 'create':
            return LoanCreateSerializer
        else:
            return LoanDetailSerializer
    
    def perform_create(self, serializer):
        """Cria o empréstimo e gera as parcelas automaticamente."""
        loan = serializer.save(tenant=self.request.tenant)
        self._generate_installments(loan)
    
    def _generate_installments(self, loan):
        """Gera as parcelas do empréstimo baseado nos dados contratuais."""
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        installments = []
        current_date = loan.first_installment_date
        installment_amount = loan.installment_amount
        
        for i in range(1, loan.number_of_installments + 1):
            installment = Installment(
                tenant=loan.tenant,
                loan=loan,
                installment_number=i,
                due_date=current_date,
                amount_due=installment_amount
            )
            installments.append(installment)
            # Próxima parcela em 30 dias
            current_date += relativedelta(months=1)
        
        Installment.objects.bulk_create(installments)
    
    @action(detail=True, methods=['get'])
    def installments(self, request, pk=None):
        """Endpoint para listar as parcelas de um empréstimo."""
        loan = self.get_object()
        installments = loan.installments.all()
        serializer = InstallmentSerializer(installments, many=True)
        return Response(serializer.data)


class InstallmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de parcelas.
    
    Permite consulta e filtragem de parcelas, principalmente
    para controle de pagamentos e cobranças.
    """
    
    serializer_class = InstallmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'loan', 'due_date']
    ordering_fields = ['due_date', 'installment_number']
    ordering = ['due_date']
    
    def get_queryset(self):
        """Filtra parcelas pelo tenant atual."""
        return Installment.objects.filter(
            tenant=self.request.tenant
        ).select_related('loan__customer')
    
    @action(detail=False)
    def overdue(self, request):
        """Endpoint para listar parcelas vencidas."""
        from django.utils import timezone
        
        overdue_installments = self.get_queryset().filter(
            due_date__lt=timezone.now().date(),
            status__in=[
                Installment.InstallmentStatus.PENDING,
                Installment.InstallmentStatus.PARTIALLY_PAID
            ]
        )
        
        serializer = self.get_serializer(overdue_installments, many=True)
        return Response(serializer.data)