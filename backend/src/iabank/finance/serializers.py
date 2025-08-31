"""
Serializers do app Finance.

Define os serializers para transformação de dados entre
representações JSON da API e modelos Django do app financeiro.
"""

from rest_framework import serializers
from .models import BankAccount, PaymentCategory, CostCenter, Supplier, FinancialTransaction


class BankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer para contas bancárias.
    
    Inclui saldo atual calculado para exibição
    nas interfaces de usuário.
    """
    
    current_balance = serializers.ReadOnlyField()
    
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'name',
            'bank_name',
            'agency',
            'account_number',
            'initial_balance',
            'current_balance',
            'is_active',
            'created_at'
        ]


class PaymentCategorySerializer(serializers.ModelSerializer):
    """Serializer para categorias de pagamento."""
    
    class Meta:
        model = PaymentCategory
        fields = [
            'id',
            'name',
            'description',
            'is_active'
        ]


class CostCenterSerializer(serializers.ModelSerializer):
    """Serializer para centros de custo."""
    
    class Meta:
        model = CostCenter
        fields = [
            'id',
            'code',
            'name',
            'description',
            'is_active'
        ]


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para fornecedores."""
    
    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'document_number',
            'email',
            'phone',
            'address',
            'is_active'
        ]


class FinancialTransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de transações financeiras.
    
    Otimizado para performance em listas, incluindo apenas
    campos essenciais e nomes de related models.
    """
    
    bank_account_name = serializers.CharField(source='bank_account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id',
            'description',
            'amount',
            'type',
            'transaction_date',
            'due_date',
            'is_paid',
            'payment_date',
            'status_display',
            'is_overdue',
            'bank_account_name',
            'category_name',
            'supplier_name'
        ]


class FinancialTransactionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para detalhes completos de uma transação financeira.
    
    Inclui todas as informações e relacionamentos
    para visualização e edição completa.
    """
    
    status_display = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'id',
            'description',
            'amount',
            'type',
            'transaction_date',
            'due_date',
            'is_paid',
            'payment_date',
            'status_display',
            'is_overdue',
            'bank_account',
            'category',
            'cost_center',
            'supplier',
            'installment',
            'notes',
            'created_at',
            'updated_at'
        ]


class FinancialTransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de transações financeiras.
    
    Inclui validações específicas para criação e
    campos obrigatórios.
    """
    
    class Meta:
        model = FinancialTransaction
        fields = [
            'description',
            'amount',
            'type',
            'transaction_date',
            'due_date',
            'bank_account',
            'category',
            'cost_center',
            'supplier',
            'notes'
        ]
        
    def validate_bank_account(self, value):
        """Valida se a conta bancária pertence ao tenant atual e está ativa."""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if value.tenant != request.tenant:
                raise serializers.ValidationError(
                    "Conta bancária não pertence ao tenant atual."
                )
            if not value.is_active:
                raise serializers.ValidationError(
                    "Conta bancária não está ativa."
                )
        return value
        
    def validate_category(self, value):
        """Valida se a categoria pertence ao tenant atual."""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'tenant'):
                if value.tenant != request.tenant:
                    raise serializers.ValidationError(
                        "Categoria não pertence ao tenant atual."
                    )
        return value
        
    def validate_supplier(self, value):
        """Valida se o fornecedor pertence ao tenant atual."""
        if value:
            request = self.context.get('request')
            if request and hasattr(request, 'tenant'):
                if value.tenant != request.tenant:
                    raise serializers.ValidationError(
                        "Fornecedor não pertence ao tenant atual."
                    )
        return value