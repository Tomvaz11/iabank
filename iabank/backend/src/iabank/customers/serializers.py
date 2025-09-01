"""
Serializers do app Customers.

Define os serializers para transformação de dados entre
representações JSON da API e modelos Django do app de clientes.
"""

from rest_framework import serializers
from .models import Customer


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de clientes.
    
    Inclui apenas campos essenciais para exibição em listas,
    otimizando performance e reduzindo payload.
    """
    
    primary_contact = serializers.ReadOnlyField()
    
    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'document_number', 
            'email',
            'primary_contact',
            'city',
            'is_active',
            'created_at'
        ]


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para detalhes completos de um cliente.
    
    Inclui todos os campos disponíveis para visualização
    e edição completa dos dados do cliente.
    """
    
    full_address = serializers.ReadOnlyField()
    primary_contact = serializers.ReadOnlyField()
    
    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'document_number',
            'birth_date',
            'email',
            'phone',
            'mobile_phone',
            'primary_contact',
            'zip_code',
            'street',
            'number',
            'complement',
            'neighborhood',
            'city',
            'state',
            'full_address',
            'is_active',
            'notes',
            'created_at',
            'updated_at'
        ]


class CustomerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novos clientes.
    
    Inclui validações específicas para criação e
    campos obrigatórios mínimos.
    """
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'document_number',
            'birth_date',
            'email',
            'phone',
            'mobile_phone',
            'zip_code',
            'street',
            'number',
            'complement',
            'neighborhood',
            'city',
            'state',
            'notes'
        ]
        
    def validate_document_number(self, value):
        """Valida se o documento já existe para o tenant atual."""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if Customer.objects.filter(
                tenant=request.tenant,
                document_number=value
            ).exists():
                raise serializers.ValidationError(
                    "Já existe um cliente com este documento."
                )
        return value