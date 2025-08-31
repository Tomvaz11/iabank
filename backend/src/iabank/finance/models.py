"""
Modelos de dados do app Finance.

Define as entidades financeiras: BankAccount, PaymentCategory, 
CostCenter, Supplier e FinancialTransaction para controle
financeiro completo da organização.
"""

from django.db import models
from decimal import Decimal
from iabank.core.models import BaseTenantModel


class BankAccount(BaseTenantModel):
    """
    Modelo que representa uma conta bancária da organização.
    
    Controla as contas bancárias utilizadas para movimentações
    financeiras e reconciliação bancária.
    """
    
    name = models.CharField(max_length=100, verbose_name="Nome da conta")
    bank_name = models.CharField(max_length=100, verbose_name="Nome do banco")
    agency = models.CharField(max_length=10, blank=True, verbose_name="Agência")
    account_number = models.CharField(max_length=20, verbose_name="Número da conta")
    initial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo inicial"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Conta bancária"
        verbose_name_plural = "Contas bancárias"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.bank_name}"

    @property
    def current_balance(self):
        """Calcula o saldo atual baseado nas transações."""
        from django.db.models import Sum, Case, When, DecimalField
        
        transactions_sum = self.transactions.aggregate(
            total=Sum(
                Case(
                    When(type=FinancialTransaction.TransactionType.INCOME, then='amount'),
                    When(type=FinancialTransaction.TransactionType.EXPENSE, then=-1 * models.F('amount')),
                    default=0,
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
        )['total'] or Decimal('0.00')
        
        return self.initial_balance + transactions_sum


class PaymentCategory(BaseTenantModel):
    """
    Modelo que representa uma categoria de pagamento.
    
    Organiza as transações financeiras por tipo/categoria
    para facilitar relatórios e controle financeiro.
    """
    
    name = models.CharField(max_length=100, verbose_name="Nome da categoria")
    description = models.TextField(blank=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Categoria de pagamento"
        verbose_name_plural = "Categorias de pagamento"
        ordering = ['name']

    def __str__(self):
        return self.name


class CostCenter(BaseTenantModel):
    """
    Modelo que representa um centro de custo.
    
    Permite classificar gastos por departamento, projeto
    ou área específica para controle gerencial.
    """
    
    name = models.CharField(max_length=100, verbose_name="Nome do centro de custo")
    code = models.CharField(max_length=20, verbose_name="Código")
    description = models.TextField(blank=True, verbose_name="Descrição")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Centro de custo"
        verbose_name_plural = "Centros de custo"
        unique_together = [['tenant', 'code']]
        ordering = ['code', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Supplier(BaseTenantModel):
    """
    Modelo que representa um fornecedor.
    
    Mantém informações de contato e dados de fornecedores
    para controle de contas a pagar e relacionamento comercial.
    """
    
    name = models.CharField(max_length=255, verbose_name="Nome do fornecedor")
    document_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="CNPJ/CPF"
    )
    email = models.EmailField(null=True, blank=True, verbose_name="E-mail")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    address = models.TextField(blank=True, verbose_name="Endereço")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.document_number})" if self.document_number else self.name


class FinancialTransaction(BaseTenantModel):
    """
    Modelo que representa uma transação financeira.
    
    Controla todas as movimentações financeiras da organização,
    incluindo receitas e despesas com suas classificações.
    """
    
    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'

    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor"
    )
    transaction_date = models.DateField(verbose_name="Data da transação")
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de vencimento"
    )
    
    # Status de pagamento
    is_paid = models.BooleanField(default=False, verbose_name="Pago")
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data do pagamento"
    )
    
    # Tipo e classificações
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name="Tipo"
    )
    
    # Relacionamentos
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="Conta bancária"
    )
    category = models.ForeignKey(
        PaymentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Categoria"
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Centro de custo"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Fornecedor"
    )
    
    # Link para parcela de empréstimo (receitas)
    installment = models.OneToOneField(
        'operations.Installment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction',
        verbose_name="Parcela"
    )
    
    # Observações
    notes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Transação financeira"
        verbose_name_plural = "Transações financeiras"
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        type_symbol = "+" if self.type == self.TransactionType.INCOME else "-"
        return f"{type_symbol} R$ {self.amount:,.2f} - {self.description}"

    @property
    def is_overdue(self):
        """Verifica se a transação está vencida."""
        if self.is_paid or not self.due_date:
            return False
        
        from django.utils import timezone
        return self.due_date < timezone.now().date()

    @property
    def status_display(self):
        """Retorna o status da transação para exibição."""
        if self.is_paid:
            return "Pago"
        elif self.is_overdue:
            return "Vencido"
        else:
            return "Pendente"