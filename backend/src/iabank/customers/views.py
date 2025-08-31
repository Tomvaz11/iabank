"""
Views do app Customers.

Implementa os endpoints da API REST para gestão de clientes,
seguindo padrões RESTful e integrando com sistema de autenticação.
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Customer
from .serializers import (
    CustomerListSerializer,
    CustomerDetailSerializer,
    CustomerCreateSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD completas de clientes.
    
    Fornece endpoints para listar, criar, visualizar, atualizar
    e excluir clientes, com filtros e busca integrados.
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'city', 'state']
    search_fields = ['name', 'document_number', 'email', 'phone', 'mobile_phone']
    ordering_fields = ['name', 'created_at', 'city']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtra clientes pelo tenant atual."""
        return Customer.objects.filter(tenant=self.request.tenant)
    
    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action."""
        if self.action == 'list':
            return CustomerListSerializer
        elif self.action == 'create':
            return CustomerCreateSerializer
        else:
            return CustomerDetailSerializer
    
    def perform_create(self, serializer):
        """Associa o cliente ao tenant atual na criação."""
        serializer.save(tenant=self.request.tenant)