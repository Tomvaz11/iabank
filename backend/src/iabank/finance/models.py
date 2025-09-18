"""Modelos do módulo financeiro do IABANK."""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Dict, Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q

from iabank.core.fields import EncryptedCharField, EncryptedEmailField
from iabank.core.models import BaseTenantModel, _normalize_cnpj


BACEN_REGISTERED_BANKS: Dict[str, str] = {
    "001": "Banco do Brasil S.A.",
    "033": "Banco Santander (Brasil) S.A.",
    "070": "Banco de Brasília S.A.",
    "077": "Banco Inter S.A.",
    "104": "Caixa Econômica Federal",
    "212": "Banco Original S.A.",
    "237": "Banco Bradesco S.A.",
    "260": "Nu Pagamentos S.A.",
    "341": "Itaú Unibanco S.A.",
    "422": "Banco Safra S.A.",
    "623": "Banco PAN S.A.",
    "633": "Banco Rendimento S.A.",
    "652": "Itaú Unibanco Holding S.A.",
    "707": "Banco Daycoval S.A.",
    "756": "Bancoob (Banco Cooperativo do Brasil)",
}


_CPF_INVALID_SEQUENCES = {str(i) * 11 for i in range(10)}


class AccountType(models.TextChoices):
    """Tipos de contas bancárias suportadas."""

    CHECKING = "CHECKING", "Conta corrente"
    SAVINGS = "SAVINGS", "Conta poupança"
    INVESTMENT = "INVESTMENT", "Conta investimento"


class TransactionType(models.TextChoices):
    """Tipos de transações financeiras."""

    INCOME = "INCOME", "Receita"
    EXPENSE = "EXPENSE", "Despesa"


class TransactionStatus(models.TextChoices):
    """Status possíveis para transações financeiras."""

    PENDING = "PENDING", "Pendente"
    PAID = "PAID", "Pago"
    CANCELLED = "CANCELLED", "Cancelado"


class PaymentCategoryType(models.TextChoices):
    """Tipos de categorias de pagamento."""

    INCOME = "INCOME", "Receita"
    EXPENSE = "EXPENSE", "Despesa"
    BOTH = "BOTH", "Ambos"


class SupplierDocumentType(models.TextChoices):
    """Tipos de documento aceitos para fornecedores."""

    CPF = "CPF", "CPF"
    CNPJ = "CNPJ", "CNPJ"


def _normalize_cpf(value: str) -> str:
    """Normaliza e valida um CPF."""

    if not value:
        raise ValidationError({"document": "CPF é obrigatório"})

    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        raise ValidationError({"document": "CPF deve conter 11 dígitos"})

    if digits in _CPF_INVALID_SEQUENCES:
        raise ValidationError({"document": "CPF inválido"})

    def _calc_digit(sequence: str) -> str:
        total = sum(int(num) * weight for num, weight in zip(sequence, range(len(sequence) + 1, 1, -1)))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = _calc_digit(digits[:9])
    second_digit = _calc_digit(digits[:10])

    if digits[9] != first_digit or digits[10] != second_digit:
        raise ValidationError({"document": "CPF inválido"})

    return digits


def _build_sha256_hash(*parts: object) -> str:
    """Gera hash SHA-256 a partir de múltiplas partes."""

    sha = hashlib.sha256()
    for part in parts:
        if part is None:
            continue
        if isinstance(part, bytes):
            sha.update(part)
            continue
        sha.update(str(part).encode("utf-8"))
    return sha.hexdigest()


class BankAccount(BaseTenantModel):
    """Contas bancárias corporativas do tenant."""

    bank_code = models.CharField(
        max_length=10,
        help_text="Código do banco conforme tabela Bacen",
    )
    bank_name = models.CharField(
        max_length=100,
        help_text="Nome do banco",
    )
    agency = EncryptedCharField(
        max_length=20,
        help_text="Número da agência bancária",
    )
    account_number = EncryptedCharField(
        max_length=30,
        help_text="Número da conta bancária",
    )
    account_type = models.CharField(
        max_length=15,
        choices=AccountType.choices,
        default=AccountType.CHECKING,
        help_text="Tipo da conta bancária",
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Saldo atual da conta",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se a conta está ativa para movimentações",
    )
    is_main = models.BooleanField(
        default=False,
        help_text="Define se a conta é a principal do tenant",
    )
    account_identifier_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text="Hash do identificador único da conta",
    )

    class Meta:
        db_table = "finance_bank_accounts"
        ordering = ["bank_code", "bank_name"]
        indexes = [
            models.Index(
                fields=["tenant_id", "bank_code"],
                name="fin_bank_tenant_bank_code_idx",
            ),
            models.Index(
                fields=["tenant_id", "is_active"],
                name="fin_bank_tenant_active_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "account_identifier_hash"],
                name="fin_bank_unique_account_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["tenant_id"],
                condition=Q(is_main=True),
                name="fin_bank_unique_main_per_tenant",
            ),
        ]

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        try:
            normalized_bank_code = self._normalize_bank_code(self.bank_code)
        except ValidationError as exc:
            errors.update(exc.message_dict)
        else:
            self.bank_code = normalized_bank_code
            bank_lookup = BACEN_REGISTERED_BANKS.get(normalized_bank_code)
            if not bank_lookup:
                errors["bank_code"] = "Código de banco não encontrado na lista do Bacen"
            elif not self.bank_name:
                self.bank_name = bank_lookup
            else:
                self.bank_name = self.bank_name.strip()

        if self.agency:
            self.agency = self._normalize_agency(self.agency)
        else:
            errors["agency"] = "Agência bancária é obrigatória"

        if self.account_number:
            self.account_number = self._normalize_account_number(self.account_number)
        else:
            errors["account_number"] = "Número da conta é obrigatório"

        if self.bank_code and self.agency and self.account_number and self.tenant_id:
            self.account_identifier_hash = _build_sha256_hash(
                self.tenant_id,
                self.bank_code,
                self.agency,
                self.account_number,
            )
            duplicate_exists = (
                BankAccount.objects.filter(
                    tenant_id=self.tenant_id,
                    account_identifier_hash=self.account_identifier_hash,
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicate_exists:
                errors["account_number"] = "Conta bancária já cadastrada para este tenant"

        if self.is_main:
            existing_main = (
                BankAccount.objects.filter(tenant_id=self.tenant_id, is_main=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if existing_main:
                errors["is_main"] = "Já existe uma conta principal cadastrada para este tenant"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def _normalize_bank_code(self, value: str | None) -> str:
        if not value:
            raise ValidationError({"bank_code": "Código do banco é obrigatório"})
        digits = re.sub(r"\D", "", value)
        if not digits:
            raise ValidationError({"bank_code": "Código do banco inválido"})
        return digits.zfill(3)

    @staticmethod
    def _normalize_agency(value: str) -> str:
        return re.sub(r"\D", "", value).lstrip("0") or "0"

    @staticmethod
    def _normalize_account_number(value: str) -> str:
        digits_only = re.sub(r"\D", "", value or "")
        return digits_only or value.strip()

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "bank_code": self.bank_code,
                "bank_name": self.bank_name,
                "account_type": self.account_type,
                "is_main": self.is_main,
            }
        )
        return fields

    def __str__(self) -> str:
        return f"BankAccount({self.bank_code}-{self.agency})"


class PaymentCategory(BaseTenantModel):
    """Categorias de pagamentos e receitas."""

    name = models.CharField(
        max_length=100,
        help_text="Nome da categoria",
    )
    type = models.CharField(
        max_length=10,
        choices=PaymentCategoryType.choices,
        help_text="Tipo da categoria",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se a categoria esta ativa",
    )

    class Meta:
        db_table = "finance_payment_categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "name"],
                name="fin_paycat_unique_name_per_tenant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant_id", "type"],
                name="fin_paycat_tenant_type_idx",
            ),
            models.Index(
                fields=["tenant_id", "is_active"],
                name="fin_paycat_tenant_active_idx",
            ),
        ]

    def clean(self):
        super().clean()
        errors: dict[str, str] = {}

        if self.name:
            self.name = self.name.strip()
        else:
            errors["name"] = "Nome da categoria e obrigatorio"

        if not self.type:
            errors["type"] = "Tipo da categoria e obrigatorio"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "name": self.name,
                "type": self.type,
                "is_active": self.is_active,
            }
        )
        return fields

    def __str__(self) -> str:
        return f"PaymentCategory({self.name})"


class CostCenter(BaseTenantModel):
    """Centros de custo para controle gerencial."""

    code = models.CharField(
        max_length=20,
        help_text="Codigo interno do centro de custo",
    )
    name = models.CharField(
        max_length=100,
        help_text="Nome do centro de custo",
    )
    description = models.TextField(
        blank=True,
        help_text="Descricao opcional",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se o centro esta ativo",
    )

    class Meta:
        db_table = "finance_cost_centers"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "code"],
                name="fin_cost_center_unique_code",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant_id", "is_active"],
                name="fin_cost_center_active_idx",
            )
        ]

    def clean(self):
        super().clean()
        errors: dict[str, str] = {}

        if self.code:
            self.code = self.code.strip().upper()
        else:
            errors["code"] = "Codigo e obrigatorio"

        if self.name:
            self.name = self.name.strip()
        else:
            errors["name"] = "Nome e obrigatorio"

        if self.description:
            self.description = self.description.strip()

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "code": self.code,
                "name": self.name,
                "is_active": self.is_active,
            }
        )
        return fields

    def __str__(self) -> str:
        return f"CostCenter({self.code})"


class Supplier(BaseTenantModel):
    """Fornecedores cadastrados para controle de despesas."""

    document_type = models.CharField(
        max_length=5,
        choices=SupplierDocumentType.choices,
        help_text="Tipo de documento (CPF/CNPJ)",
    )
    document = EncryptedCharField(
        max_length=32,
        help_text="Documento do fornecedor armazenado de forma criptografada",
    )
    document_hash = models.CharField(
        max_length=64,
        editable=False,
        help_text="Hash do documento para garantir unicidade",
    )
    name = EncryptedCharField(
        max_length=255,
        help_text="Nome ou razao social do fornecedor",
    )
    email = EncryptedEmailField(
        blank=True,
        help_text="Email de contato do fornecedor",
    )
    phone = EncryptedCharField(
        max_length=32,
        blank=True,
        help_text="Telefone de contato do fornecedor",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica se o fornecedor esta ativo",
    )

    class Meta:
        db_table = "finance_suppliers"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "document_hash"],
                name="fin_supplier_unique_document",
            )
        ]
        indexes = [
            models.Index(
                fields=["tenant_id", "is_active"],
                name="fin_supplier_active_idx",
            )
        ]

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        try:
            normalized_document = self._normalize_document(self.document_type, self.document)
        except ValidationError as exc:
            errors.update(exc.message_dict)
            normalized_document = None

        if self.name:
            self.name = self.name.strip()
        else:
            errors["name"] = "Nome do fornecedor e obrigatorio"

        if self.email:
            self.email = self.email.strip().lower()

        if self.phone:
            self.phone = re.sub(r"\D", "", self.phone)

        if normalized_document and self.tenant_id:
            self.document = normalized_document
            self.document_hash = _build_sha256_hash(self.tenant_id, normalized_document)
            duplicate_exists = (
                Supplier.objects.filter(
                    tenant_id=self.tenant_id,
                    document_hash=self.document_hash,
                )
                .exclude(pk=self.pk)
                .exists()
            )
            if duplicate_exists:
                errors["document"] = "Fornecedor ja cadastrado para este tenant"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "document_type": self.document_type,
                "document_hash": self.document_hash,
                "is_active": self.is_active,
            }
        )
        return fields

    @staticmethod
    def _normalize_document(document_type: str | None, value: str | None) -> str:
        if document_type == SupplierDocumentType.CNPJ:
            return _normalize_cnpj(value)
        if document_type == SupplierDocumentType.CPF:
            return _normalize_cpf(value or "")
        raise ValidationError({"document_type": "Tipo de documento invalido"})

    def __str__(self) -> str:
        return f"Supplier({self.name})"


class FinancialTransaction(BaseTenantModel):
    """Transações financeiras (receitas/despesas) com categorização."""

    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="Conta bancária utilizada na transação",
    )
    installment = models.ForeignKey(
        "operations.Installment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_transactions",
        help_text="Parcela associada (para receitas)",
    )
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        help_text="Tipo da transação (receita/ despesa)",
    )
    category = models.ForeignKey(
        "finance.PaymentCategory",
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="Categoria de classificação",
    )
    cost_center = models.ForeignKey(
        "finance.CostCenter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Centro de custo associado",
    )
    supplier = models.ForeignKey(
        "finance.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="Fornecedor associado (para despesas)",
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Valor da transação",
    )
    description = models.CharField(
        max_length=255,
        help_text="Descrição breve da transação",
    )
    reference_date = models.DateField(
        help_text="Data de competência da transação",
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Data de vencimento (para despesas futuras)",
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Data de pagamento",
    )
    status = models.CharField(
        max_length=12,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        help_text="Status atual da transação",
    )
    document_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Documento de referência (NF, recibo, etc)",
    )

    class Meta:
        db_table = "finance_financial_transactions"
        ordering = ["-reference_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "type"],
                name="fin_trans_tenant_type_idx",
            ),
            models.Index(
                fields=["tenant_id", "status"],
                name="fin_trans_tenant_status_idx",
            ),
            models.Index(
                fields=["tenant_id", "reference_date"],
                name="fin_trans_tenant_reference_idx",
            ),
        ]

    def clean(self):
        super().clean()

        errors: dict[str, str] = {}

        if self.description:
            self.description = self.description.strip()

        if self.document_number:
            self.document_number = self.document_number.strip()

        if not self.amount or self.amount <= Decimal("0"):
            errors["amount"] = "Valor da transação deve ser maior que zero"

        tenant_id = self.tenant_id or getattr(self.bank_account, "tenant_id", None)
        if tenant_id is None:
            errors["tenant_id"] = "tenant_id é obrigatório para transações"
        else:
            self.tenant_id = tenant_id

        if self.bank_account and self.bank_account.tenant_id != self.tenant_id:
            errors["bank_account"] = "Conta bancária deve pertencer ao mesmo tenant"

        if self.category and self.category.tenant_id != self.tenant_id:
            errors["category"] = "Categoria deve pertencer ao mesmo tenant"
        elif self.category:
            if self.type == TransactionType.INCOME and self.category.type == PaymentCategoryType.EXPENSE:
                errors["category"] = "Categoria de despesa não pode ser usada em receita"
            if self.type == TransactionType.EXPENSE and self.category.type == PaymentCategoryType.INCOME:
                errors["category"] = "Categoria de receita não pode ser usada em despesa"

        if self.cost_center and self.cost_center.tenant_id != self.tenant_id:
            errors["cost_center"] = "Centro de custo deve pertencer ao mesmo tenant"

        if self.supplier:
            if self.supplier.tenant_id != self.tenant_id:
                errors["supplier"] = "Fornecedor deve pertencer ao mesmo tenant"
        elif self.type == TransactionType.EXPENSE:
            errors["supplier"] = "Fornecedor é obrigatório para despesas"

        if self.installment:
            if self.installment.tenant_id != self.tenant_id:
                errors["installment"] = "Parcela deve pertencer ao mesmo tenant"
            if self.type != TransactionType.INCOME:
                errors["installment"] = "Parcela só pode ser associada a receitas"

        if self.status == TransactionStatus.PAID and not self.payment_date:
            errors["payment_date"] = "Data de pagamento é obrigatória para transações pagas"

        if self.payment_date and self.status != TransactionStatus.PAID:
            errors["status"] = "Transações com data de pagamento devem estar com status PAID"

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        previous_state: Optional[FinancialTransaction] = None
        if not is_create and self.pk:
            previous_state = FinancialTransaction.objects.select_related("bank_account").get(pk=self.pk)

        self.full_clean()

        previous_bank_account_id: Optional[str] = None
        previous_delta = Decimal("0.00")
        if previous_state:
            previous_bank_account_id = previous_state.bank_account_id
            previous_delta = previous_state._calculate_balance_delta()

        new_delta = self._calculate_balance_delta()

        super().save(*args, **kwargs)

        self._apply_balance_updates(previous_bank_account_id, previous_delta, new_delta)

    def delete(self, *args, **kwargs):
        delta = self._calculate_balance_delta()
        bank_account_id = self.bank_account_id
        tenant_id = self.tenant_id
        super().delete(*args, **kwargs)
        if bank_account_id:
            BankAccount.objects.filter(pk=bank_account_id, tenant_id=tenant_id).update(
                balance=F("balance") - delta
            )

    def _calculate_balance_delta(self) -> Decimal:
        if not self.amount:
            return Decimal("0.00")
        if self.type == TransactionType.INCOME:
            return self.amount
        return self.amount * Decimal("-1")

    def _apply_balance_updates(
        self,
        previous_bank_account_id: Optional[str],
        previous_delta: Decimal,
        new_delta: Decimal,
    ) -> None:
        with transaction.atomic():
            if previous_bank_account_id and previous_bank_account_id != self.bank_account_id:
                BankAccount.objects.filter(
                    pk=previous_bank_account_id,
                    tenant_id=self.tenant_id,
                ).update(balance=F("balance") - previous_delta)
                BankAccount.objects.filter(
                    pk=self.bank_account_id,
                    tenant_id=self.tenant_id,
                ).update(balance=F("balance") + new_delta)
                return

            net_delta = new_delta - previous_delta
            if net_delta == Decimal("0.00"):
                return

            BankAccount.objects.filter(
                pk=self.bank_account_id,
                tenant_id=self.tenant_id,
            ).update(balance=F("balance") + net_delta)

    def get_audit_fields(self):  # type: ignore[override]
        fields = super().get_audit_fields()
        fields.update(
            {
                "type": self.type,
                "amount": str(self.amount),
                "status": self.status,
                "bank_account_id": str(self.bank_account_id) if self.bank_account_id else None,
            }
        )
        return fields

    def __str__(self) -> str:
        return f"FinancialTransaction({self.type}, {self.amount})"
