"""Entidades de domínio para o módulo financeiro."""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)


MONEY_QUANTIZER = Decimal("0.01")


BACEN_REGISTERED_BANKS = {
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
_CNPJ_INVALID_SEQUENCES = {str(i) * 14 for i in range(10)}


class AccountType(StrEnum):
    """Tipos de conta bancária suportadas."""

    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"
    INVESTMENT = "INVESTMENT"


class TransactionType(StrEnum):
    """Tipos de transação financeira."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionStatus(StrEnum):
    """Status possíveis para transação financeira."""

    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentCategoryType(StrEnum):
    """Tipos de categoria de pagamento."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    BOTH = "BOTH"


class SupplierDocumentType(StrEnum):
    """Documentos aceitos para fornecedores."""

    CPF = "CPF"
    CNPJ = "CNPJ"


def _build_sha256_hash(*parts: object) -> str:
    """Gera hash SHA-256 determinístico a partir de múltiplas partes."""

    digest = hashlib.sha256()
    for part in parts:
        if part is None:
            continue
        if isinstance(part, bytes):
            digest.update(part)
            continue
        digest.update(str(part).encode("utf-8"))
    return digest.hexdigest()


def _normalize_bank_code(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if not digits:
        raise ValueError("Código do banco é obrigatório")
    return digits.zfill(3)


def _normalize_agency(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    cleaned = digits.lstrip("0")
    return cleaned or "0"


def _normalize_account_number(value: str) -> str:
    digits_only = re.sub(r"\D", "", value or "")
    return digits_only or (value or "").strip()


def _normalize_cpf(value: str | None) -> str:
    if not value:
        raise ValueError("CPF é obrigatório")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos")

    if digits in _CPF_INVALID_SEQUENCES:
        raise ValueError("CPF inválido")

    def _calc_digit(sequence: str) -> str:
        weights = range(len(sequence) + 1, 1, -1)
        total = sum(int(num) * weight for num, weight in zip(sequence, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = _calc_digit(digits[:9])
    second_digit = _calc_digit(digits[:10])

    if digits[9] != first_digit or digits[10] != second_digit:
        raise ValueError("CPF inválido")

    return digits


def _normalize_cnpj(value: str | None) -> str:
    if not value:
        raise ValueError("CNPJ é obrigatório")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos")

    if digits in _CNPJ_INVALID_SEQUENCES:
        raise ValueError("CNPJ inválido")

    def _calc_digit(sequence: str, weights: list[int]) -> str:
        total = sum(int(num) * weight for num, weight in zip(sequence, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first_digit = _calc_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = _calc_digit(digits[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])

    if digits[12] != first_digit or digits[13] != second_digit:
        raise ValueError("CNPJ inválido")

    return digits


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


class BankAccountEntity(BaseModel):
    """Entidade de domínio representando conta bancária corporativa."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID
    bank_code: str
    bank_name: Optional[str] = None
    agency: str
    account_number: str
    account_type: AccountType = AccountType.CHECKING
    balance: Decimal = Field(default=Decimal("0.00"))
    is_active: bool = True
    is_main: bool = False
    account_identifier_hash: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("bank_code", mode="before")
    @classmethod
    def _normalize_bank_code_validator(cls, value: str) -> str:
        return _normalize_bank_code(value)

    @field_validator("bank_name", mode="before")
    @classmethod
    def _normalize_bank_name(cls, value: Optional[str], info: ValidationInfo) -> Optional[str]:
        if value is None or not value.strip():
            bank_code = (info.data or {}).get("bank_code")
            if bank_code in BACEN_REGISTERED_BANKS:
                return BACEN_REGISTERED_BANKS[bank_code]
            return value
        return value.strip()

    @field_validator("agency", mode="before")
    @classmethod
    def _normalize_agency_validator(cls, value: str) -> str:
        if not value:
            raise ValueError("Agência bancária é obrigatória")
        return _normalize_agency(value)

    @field_validator("account_number", mode="before")
    @classmethod
    def _normalize_account_number_validator(cls, value: str) -> str:
        if not value:
            raise ValueError("Número da conta é obrigatório")
        return _normalize_account_number(value)

    @field_validator("balance", mode="before")
    @classmethod
    def _normalize_balance(cls, value: Decimal | int | float) -> Decimal:
        decimal_value = Decimal(value)
        return _quantize_money(decimal_value)

    @model_validator(mode="after")
    def _validate_bank(self) -> "BankAccountEntity":
        if self.bank_code not in BACEN_REGISTERED_BANKS:
            raise ValueError("Código de banco não está cadastrado no Bacen")

        identifier = _build_sha256_hash(
            self.tenant_id,
            self.bank_code,
            self.agency,
            self.account_number,
        )
        object.__setattr__(self, "account_identifier_hash", identifier)
        return self

    def with_balance(self, balance: Decimal) -> "BankAccountEntity":
        return self.model_copy(update={"balance": _quantize_money(balance)}, validate=True)


class PaymentCategoryEntity(BaseModel):
    """Entidade de domínio para categorias de pagamento."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID
    name: str
    type: PaymentCategoryType
    is_active: bool = True
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Nome da categoria é obrigatório")
        return value.strip()


class CostCenterEntity(BaseModel):
    """Entidade de domínio para centros de custo."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Código do centro de custo é obrigatório")
        return value.strip().upper()

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Nome do centro de custo é obrigatório")
        return value.strip()

    @field_validator("description")
    @classmethod
    def _normalize_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class SupplierEntity(BaseModel):
    """Entidade de domínio representando fornecedores."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID
    document_type: SupplierDocumentType
    document: str
    document_hash: Optional[str] = Field(default=None)
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("document", mode="before")
    @classmethod
    def _normalize_document(cls, value: str, info: ValidationInfo) -> str:
        document_type = (info.data or {}).get("document_type")
        if document_type == SupplierDocumentType.CNPJ:
            return _normalize_cnpj(value)
        if document_type == SupplierDocumentType.CPF:
            return _normalize_cpf(value)
        raise ValueError("Tipo de documento inválido para fornecedor")

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Nome do fornecedor é obrigatório")
        return value.strip()

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip().lower()
        return cleaned or None

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        digits = re.sub(r"\D", "", value)
        return digits or None

    @model_validator(mode="after")
    def _populate_hash(self) -> "SupplierEntity":
        document_hash = _build_sha256_hash(self.tenant_id, self.document)
        object.__setattr__(self, "document_hash", document_hash)
        return self


class FinancialTransactionEntity(BaseModel):
    """Entidade de domínio para transações financeiras."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
        populate_by_name=True,
    )

    id: Optional[UUID] = Field(default=None)
    tenant_id: UUID
    bank_account_id: UUID
    installment_id: Optional[UUID] = None
    type: TransactionType
    category_id: UUID
    cost_center_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    amount: Decimal
    description: str
    reference_date: date
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    status: TransactionStatus = TransactionStatus.PENDING
    document_number: Optional[str] = None
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("amount", mode="before")
    @classmethod
    def _normalize_amount(cls, value: Decimal | int | float) -> Decimal:
        decimal_value = Decimal(value)
        if decimal_value <= Decimal("0"):
            raise ValueError("Valor da transação deve ser maior que zero")
        return _quantize_money(decimal_value)

    @field_validator("description")
    @classmethod
    def _normalize_description(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Descrição da transação é obrigatória")
        return value.strip()

    @field_validator("document_number")
    @classmethod
    def _normalize_document_number(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def _validate_business_rules(self) -> "FinancialTransactionEntity":
        if self.type == TransactionType.EXPENSE and not self.supplier_id:
            raise ValueError("Fornecedor é obrigatório para despesas")

        if self.type == TransactionType.INCOME and self.supplier_id:
            raise ValueError("Fornecedor não deve ser informado para receitas")

        if self.installment_id and self.type != TransactionType.INCOME:
            raise ValueError("Parcela só pode ser associada a receitas")

        if self.payment_date and self.status != TransactionStatus.PAID:
            raise ValueError("Transações pagas devem possuir status PAID")

        if self.status == TransactionStatus.PAID and not self.payment_date:
            raise ValueError("Data de pagamento é obrigatória para transações pagas")

        if self.due_date and self.due_date < self.reference_date:
            raise ValueError("Data de vencimento não pode ser anterior à referência")

        return self

    def mark_as_paid(self, payment_date: date) -> "FinancialTransactionEntity":
        return self.model_copy(
            update={
                "status": TransactionStatus.PAID,
                "payment_date": payment_date,
            },
            validate=True,
        )

    def cancel(self) -> "FinancialTransactionEntity":
        return self.model_copy(
            update={
                "status": TransactionStatus.CANCELLED,
                "payment_date": None,
            },
            validate=True,
        )

    def balance_delta(self) -> Decimal:
        """Retorna o impacto no saldo da conta bancária."""

        if self.type == TransactionType.INCOME:
            return self.amount
        return self.amount * Decimal("-1")


__all__ = [
    "AccountType",
    "BACEN_REGISTERED_BANKS",
    "BankAccountEntity",
    "CostCenterEntity",
    "FinancialTransactionEntity",
    "MONEY_QUANTIZER",
    "PaymentCategoryEntity",
    "PaymentCategoryType",
    "SupplierDocumentType",
    "SupplierEntity",
    "TransactionStatus",
    "TransactionType",
]
