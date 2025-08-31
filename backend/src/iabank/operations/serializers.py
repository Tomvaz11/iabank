"""
Serializers do app Operations.

Define os serializers para transformação de dados entre
representações JSON da API e modelos Django do app de operações.
"""

from rest_framework import serializers
from .models import Consultant, Loan, Installment


class ConsultantSerializer(serializers.ModelSerializer):
    """
    Serializer para consultores.
    
    Inclui informações do usuário associado para
    exibição completa dos dados do consultor.
    """
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Consultant
        fields = [
            'id',
            'user_name',
            'username', 
            'balance',
            'is_active',
            'created_at'
        ]


class InstallmentSerializer(serializers.ModelSerializer):
    """
    Serializer para parcelas de empréstimo.
    
    Inclui campos calculados para facilitar exibição
    na interface do usuário.
    """
    
    remaining_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Installment
        fields = [
            'id',
            'installment_number',
            'due_date',
            'amount_due',
            'amount_paid',
            'remaining_amount',
            'payment_date',
            'status',
            'is_overdue'
        ]


class LoanListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de empréstimos.
    
    Otimizado para performance em listas, incluindo apenas
    campos essenciais e dados de related models.
    """
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    consultant_name = serializers.CharField(source='consultant.user.get_full_name', read_only=True)
    total_amount = serializers.ReadOnlyField()
    installment_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Loan
        fields = [
            'id',
            'customer_name',
            'consultant_name',
            'principal_amount',
            'total_amount',
            'installment_amount',
            'number_of_installments',
            'status',
            'contract_date',
            'created_at'
        ]


class LoanDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para detalhes completos de um empréstimo.
    
    Inclui todas as informações do empréstimo e suas parcelas
    para visualização completa.
    """
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    consultant_name = serializers.CharField(source='consultant.user.get_full_name', read_only=True)
    total_amount = serializers.ReadOnlyField()
    installment_amount = serializers.ReadOnlyField()
    installments = InstallmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id',
            'customer',
            'customer_name',
            'consultant',
            'consultant_name',
            'principal_amount',
            'interest_rate',
            'total_amount',
            'installment_amount',
            'number_of_installments',
            'contract_date',
            'first_installment_date',
            'status',
            'notes',
            'installments',
            'created_at',
            'updated_at'
        ]


class LoanCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de novos empréstimos.
    
    Inclui validações específicas para criação e
    campos obrigatórios.
    """
    
    class Meta:
        model = Loan
        fields = [
            'customer',
            'consultant',
            'principal_amount',
            'interest_rate',
            'number_of_installments',
            'contract_date',
            'first_installment_date',
            'notes'
        ]
        
    def validate_customer(self, value):
        """Valida se o cliente pertence ao tenant atual."""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if value.tenant != request.tenant:
                raise serializers.ValidationError(
                    "Cliente não pertence ao tenant atual."
                )
        return value
        
    def validate_consultant(self, value):
        """Valida se o consultor pertence ao tenant atual e está ativo."""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if value.tenant != request.tenant:
                raise serializers.ValidationError(
                    "Consultor não pertence ao tenant atual."
                )
            if not value.is_active:
                raise serializers.ValidationError(
                    "Consultor não está ativo."
                )
        return value