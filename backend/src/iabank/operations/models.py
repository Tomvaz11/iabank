"""
Modelos de dados do app Operations.

Define as entidades principais do negócio: Consultant, Loan e Installment,
implementando a lógica de domínio para operações de empréstimo.
"""

from django.db import models
from decimal import Decimal
from iabank.core.models import BaseTenantModel, User


class Consultant(BaseTenantModel):
    """
    Modelo que representa um consultor/cobrador no sistema.
    
    Cada consultor pode ter um saldo e está associado a um usuário
    para controle de acesso e operações.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo"
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Consultor"
        verbose_name_plural = "Consultores"
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.tenant.name}"


class Loan(BaseTenantModel):
    """
    Modelo que representa um empréstimo no sistema.
    
    Contém todas as informações contratuais e de controle
    necessárias para gestão completa do empréstimo.
    """
    
    class LoanStatus(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'Em Andamento'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        CANCELED = 'CANCELED', 'Cancelado'

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name="Cliente"
    )
    consultant = models.ForeignKey(
        Consultant,
        on_delete=models.PROTECT,
        related_name='loans',
        verbose_name="Consultor"
    )
    
    # Dados financeiros
    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor principal"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taxa de juros (%)"
    )
    number_of_installments = models.PositiveSmallIntegerField(
        verbose_name="Número de parcelas"
    )
    
    # Datas contratuais
    contract_date = models.DateField(verbose_name="Data do contrato")
    first_installment_date = models.DateField(verbose_name="Data da primeira parcela")
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.IN_PROGRESS,
        verbose_name="Status"
    )
    
    # Observações
    notes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"
        ordering = ['-created_at']

    def __str__(self):
        return f"Empréstimo {self.id} - {self.customer.name}"

    @property
    def total_amount(self):
        """Calcula o valor total do empréstimo com juros."""
        return self.principal_amount * (1 + self.interest_rate / 100)

    @property
    def installment_amount(self):
        """Calcula o valor de cada parcela."""
        return self.total_amount / self.number_of_installments


class Installment(BaseTenantModel):
    """
    Modelo que representa uma parcela de empréstimo.
    
    Controla os pagamentos individuais de cada parcela,
    incluindo valores, datas e status de pagamento.
    """
    
    class InstallmentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        OVERDUE = 'OVERDUE', 'Vencida'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Parcialmente Pago'

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='installments',
        verbose_name="Empréstimo"
    )
    installment_number = models.PositiveSmallIntegerField(
        verbose_name="Número da parcela"
    )
    
    # Valores
    due_date = models.DateField(verbose_name="Data de vencimento")
    amount_due = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor devido"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor pago"
    )
    
    # Controle de pagamento
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data do pagamento"
    )
    status = models.CharField(
        max_length=20,
        choices=InstallmentStatus.choices,
        default=InstallmentStatus.PENDING,
        verbose_name="Status"
    )

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"
        unique_together = [['loan', 'installment_number']]
        ordering = ['due_date']

    def __str__(self):
        return f"Parcela {self.installment_number}/{self.loan.number_of_installments} - {self.loan.customer.name}"

    @property
    def remaining_amount(self):
        """Calcula o valor restante a ser pago."""
        return self.amount_due - self.amount_paid

    @property
    def is_overdue(self):
        """Verifica se a parcela está vencida."""
        from django.utils import timezone
        return (
            self.status != self.InstallmentStatus.PAID and
            self.due_date < timezone.now().date()
        )