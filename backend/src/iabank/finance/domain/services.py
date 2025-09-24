"""Serviços de domínio para o módulo financeiro."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .entities import (
    AccountType,
    BankAccountEntity,
    CostCenterEntity,
    FinancialTransactionEntity,
    PaymentCategoryEntity,
    PaymentCategoryType,
    SupplierDocumentType,
    SupplierEntity,
    TransactionStatus,
    TransactionType,
)


class FinanceDomainError(RuntimeError):
    """Erro genérico para regras de domínio financeiro."""


class BankAccountAlreadyExistsError(FinanceDomainError):
    """Indica tentativa de cadastrar conta bancária duplicada."""


class MainBankAccountConflictError(FinanceDomainError):
    """Indica conflito ao definir conta principal do tenant."""


class PaymentCategoryAlreadyExistsError(FinanceDomainError):
    """Categoria com o mesmo nome já cadastrada para o tenant."""


class CostCenterAlreadyExistsError(FinanceDomainError):
    """Centro de custo com o mesmo código já cadastrado para o tenant."""


class SupplierAlreadyExistsError(FinanceDomainError):
    """Fornecedor com o mesmo documento já cadastrado para o tenant."""


class TenantMismatchError(FinanceDomainError):
    """Entidades relacionadas pertencem a tenants diferentes."""


class CategoryTypeMismatchError(FinanceDomainError):
    """Categoria não é compatível com o tipo de transação."""


class TransactionDomainError(FinanceDomainError):
    """Erro específico para transações financeiras."""


class BankAccountCreateInput(BaseModel):
    """Dados para criação de conta bancária."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    bank_code: str
    bank_name: Optional[str] = None
    agency: str
    account_number: str
    account_type: AccountType = AccountType.CHECKING
    is_main: bool = False

    @field_validator("bank_code")
    @classmethod
    def _strip_bank_code(cls, value: str) -> str:
        return value.strip()

    @field_validator("agency", "account_number")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class BankAccountUpdateInput(BaseModel):
    """Campos permitidos para atualização de conta bancária."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    bank_name: Optional[str] = None
    agency: Optional[str] = None
    account_number: Optional[str] = None
    account_type: Optional[AccountType] = None
    is_main: Optional[bool] = None
    is_active: Optional[bool] = None


class PaymentCategoryCreateInput(BaseModel):
    """Dados para criação de categoria financeira."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    name: str
    type: PaymentCategoryType
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        return value.strip()


class PaymentCategoryUpdateInput(BaseModel):
    """Campos permitidos para atualizar categoria."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    name: Optional[str] = None
    type: Optional[PaymentCategoryType] = None
    is_active: Optional[bool] = None


class CostCenterCreateInput(BaseModel):
    """Dados para criação de centro de custo."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_active: bool = True

    @field_validator("code", "name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class CostCenterUpdateInput(BaseModel):
    """Campos para atualizar centro de custo."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierCreateInput(BaseModel):
    """Dados necessários para criação de fornecedor."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    document_type: SupplierDocumentType
    document: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True


class SupplierUpdateInput(BaseModel):
    """Campos para atualização de fornecedor."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_type: Optional[SupplierDocumentType] = None
    document: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class FinancialTransactionCreateInput(BaseModel):
    """Dados para criação de transação financeira."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    tenant_id: UUID
    bank_account: BankAccountEntity
    category: PaymentCategoryEntity
    type: TransactionType
    amount: Decimal
    description: str
    reference_date: date
    status: TransactionStatus = TransactionStatus.PENDING
    cost_center: Optional[CostCenterEntity] = None
    supplier: Optional[SupplierEntity] = None
    installment_id: Optional[UUID] = None
    due_date: Optional[date] = None
    payment_date: Optional[date] = None
    document_number: Optional[str] = None


class FinancialTransactionUpdateInput(BaseModel):
    """Campos suportados para atualização de transações."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    description: Optional[str] = None
    status: Optional[TransactionStatus] = None
    payment_date: Optional[date] = None
    cost_center: Optional[CostCenterEntity] = None
    supplier: Optional[SupplierEntity] = None
    category: Optional[PaymentCategoryEntity] = None
    document_number: Optional[str] = None


class BankAccountService:
    """Serviços para regras de contas bancárias."""

    @classmethod
    def create(
        cls,
        data: BankAccountCreateInput,
        *,
        existing_accounts: Iterable[object] = (),
    ) -> BankAccountEntity:
        entity = BankAccountEntity(
            tenant_id=data.tenant_id,
            bank_code=data.bank_code,
            bank_name=data.bank_name,
            agency=data.agency,
            account_number=data.account_number,
            account_type=data.account_type,
            is_main=data.is_main,
        )
        cls._ensure_constraints(entity, existing_accounts)
        return entity

    @classmethod
    def update(
        cls,
        account: BankAccountEntity,
        data: BankAccountUpdateInput,
        *,
        existing_accounts: Iterable[object] = (),
    ) -> BankAccountEntity:
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
        payload = account.model_dump()
        payload.update({k: v for k, v in updates.items() if v is not None or k in {"is_active", "is_main"}})
        updated = BankAccountEntity(**payload)
        cls._ensure_constraints(updated, existing_accounts, ignore_id=account.id)
        return updated

    @classmethod
    def deactivate(cls, account: BankAccountEntity) -> BankAccountEntity:
        if not account.is_active:
            return account
        return account.model_copy(update={"is_active": False}, validate=True)

    @classmethod
    def set_as_main(
        cls,
        account: BankAccountEntity,
        *,
        existing_accounts: Iterable[object],
    ) -> BankAccountEntity:
        updated = account.model_copy(update={"is_main": True}, validate=True)
        cls._ensure_constraints(updated, existing_accounts, ignore_id=account.id)
        return updated

    @classmethod
    def _ensure_constraints(
        cls,
        candidate: BankAccountEntity,
        existing_accounts: Iterable[object],
        *,
        ignore_id: Optional[UUID] = None,
    ) -> None:
        accounts = list(cls._to_entities(existing_accounts))
        for account in accounts:
            if ignore_id and account.id == ignore_id:
                continue
            if account.account_identifier_hash == candidate.account_identifier_hash:
                raise BankAccountAlreadyExistsError("Conta bancária já cadastrada para este tenant.")

        if candidate.is_main:
            for account in accounts:
                if ignore_id and account.id == ignore_id:
                    continue
                if account.is_main:
                    raise MainBankAccountConflictError("Já existe uma conta principal cadastrada para este tenant.")

    @staticmethod
    def _to_entities(accounts: Iterable[object]) -> Iterable[BankAccountEntity]:
        for account in accounts:
            if isinstance(account, BankAccountEntity):
                yield account
            else:
                yield BankAccountEntity.model_validate(account)


class PaymentCategoryService:
    """Serviços de regras para categorias de pagamento."""

    @classmethod
    def create(
        cls,
        data: PaymentCategoryCreateInput,
        *,
        existing_categories: Iterable[object] = (),
    ) -> PaymentCategoryEntity:
        entity = PaymentCategoryEntity(
            tenant_id=data.tenant_id,
            name=data.name,
            type=data.type,
            is_active=data.is_active,
        )
        cls._ensure_unique(entity, existing_categories)
        return entity

    @classmethod
    def update(
        cls,
        category: PaymentCategoryEntity,
        data: PaymentCategoryUpdateInput,
        *,
        existing_categories: Iterable[object] = (),
    ) -> PaymentCategoryEntity:
        updates = data.model_dump(exclude_unset=True)
        payload = category.model_dump()
        payload.update({k: v for k, v in updates.items() if v is not None or k == "is_active"})
        updated = PaymentCategoryEntity(**payload)
        cls._ensure_unique(updated, existing_categories, ignore_id=category.id)
        return updated

    @classmethod
    def _ensure_unique(
        cls,
        candidate: PaymentCategoryEntity,
        categories: Iterable[object],
        *,
        ignore_id: Optional[UUID] = None,
    ) -> None:
        for category in cls._to_entities(categories):
            if ignore_id and category.id == ignore_id:
                continue
            if category.tenant_id != candidate.tenant_id:
                continue
            if category.name.casefold() == candidate.name.casefold():
                raise PaymentCategoryAlreadyExistsError("Categoria já existe para este tenant.")

    @staticmethod
    def _to_entities(categories: Iterable[object]) -> Iterable[PaymentCategoryEntity]:
        for category in categories:
            if isinstance(category, PaymentCategoryEntity):
                yield category
            else:
                yield PaymentCategoryEntity.model_validate(category)


class CostCenterService:
    """Serviços para regras de centros de custo."""

    @classmethod
    def create(
        cls,
        data: CostCenterCreateInput,
        *,
        existing_centers: Iterable[object] = (),
    ) -> CostCenterEntity:
        entity = CostCenterEntity(
            tenant_id=data.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
        )
        cls._ensure_unique(entity, existing_centers)
        return entity

    @classmethod
    def update(
        cls,
        center: CostCenterEntity,
        data: CostCenterUpdateInput,
        *,
        existing_centers: Iterable[object] = (),
    ) -> CostCenterEntity:
        updates = data.model_dump(exclude_unset=True)
        payload = center.model_dump()
        payload.update({k: v for k, v in updates.items() if v is not None or k == "is_active"})
        updated = CostCenterEntity(**payload)
        cls._ensure_unique(updated, existing_centers, ignore_id=center.id)
        return updated

    @classmethod
    def _ensure_unique(
        cls,
        candidate: CostCenterEntity,
        centers: Iterable[object],
        *,
        ignore_id: Optional[UUID] = None,
    ) -> None:
        for center in cls._to_entities(centers):
            if ignore_id and center.id == ignore_id:
                continue
            if center.tenant_id != candidate.tenant_id:
                continue
            if center.code == candidate.code:
                raise CostCenterAlreadyExistsError("Centro de custo com este código já existe.")

    @staticmethod
    def _to_entities(centers: Iterable[object]) -> Iterable[CostCenterEntity]:
        for center in centers:
            if isinstance(center, CostCenterEntity):
                yield center
            else:
                yield CostCenterEntity.model_validate(center)


class SupplierService:
    """Serviços para regras de fornecedores."""

    @classmethod
    def create(
        cls,
        data: SupplierCreateInput,
        *,
        existing_suppliers: Iterable[object] = (),
    ) -> SupplierEntity:
        entity = SupplierEntity(
            tenant_id=data.tenant_id,
            document_type=data.document_type,
            document=data.document,
            name=data.name,
            email=data.email,
            phone=data.phone,
            is_active=data.is_active,
        )
        cls._ensure_unique(entity, existing_suppliers)
        return entity

    @classmethod
    def update(
        cls,
        supplier: SupplierEntity,
        data: SupplierUpdateInput,
        *,
        existing_suppliers: Iterable[object] = (),
    ) -> SupplierEntity:
        updates = data.model_dump(exclude_unset=True)
        payload = supplier.model_dump()
        payload.update({k: v for k, v in updates.items() if v is not None or k == "is_active"})
        updated = SupplierEntity(**payload)
        cls._ensure_unique(updated, existing_suppliers, ignore_id=supplier.id)
        return updated

    @classmethod
    def _ensure_unique(
        cls,
        candidate: SupplierEntity,
        suppliers: Iterable[object],
        *,
        ignore_id: Optional[UUID] = None,
    ) -> None:
        for supplier in cls._to_entities(suppliers):
            if ignore_id and supplier.id == ignore_id:
                continue
            if supplier.tenant_id != candidate.tenant_id:
                continue
            if supplier.document_hash == candidate.document_hash:
                raise SupplierAlreadyExistsError("Fornecedor já cadastrado para este tenant.")

    @staticmethod
    def _to_entities(suppliers: Iterable[object]) -> Iterable[SupplierEntity]:
        for supplier in suppliers:
            if isinstance(supplier, SupplierEntity):
                yield supplier
            else:
                yield SupplierEntity.model_validate(supplier)


class FinancialTransactionService:
    """Serviços para regras de transações financeiras."""

    @classmethod
    def create(cls, data: FinancialTransactionCreateInput) -> FinancialTransactionEntity:
        cls._ensure_tenant_consistency(data)
        cls._ensure_category_matches_type(data.type, data.category)

        if data.type == TransactionType.EXPENSE and data.supplier is None:
            raise TransactionDomainError("Fornecedor é obrigatório para despesas.")

        if data.type == TransactionType.INCOME and data.supplier is not None:
            raise TransactionDomainError("Fornecedor não deve ser informado para receitas.")

        if data.installment_id and data.type != TransactionType.INCOME:
            raise TransactionDomainError("Parcela só pode ser associada a receitas.")

        status = data.status
        payment_date = data.payment_date
        if payment_date and status != TransactionStatus.PAID:
            status = TransactionStatus.PAID

        bank_account_id = data.bank_account.id
        if bank_account_id is None:
            raise TransactionDomainError("Conta bancária informada é inválida.")

        category_id = data.category.id
        if category_id is None:
            raise TransactionDomainError("Categoria informada é inválida.")

        cost_center_id: Optional[UUID] = None
        if data.cost_center is not None:
            if data.cost_center.id is None:
                raise TransactionDomainError("Centro de custo informado é inválido.")
            cost_center_id = data.cost_center.id

        supplier_id: Optional[UUID] = None
        if data.supplier is not None:
            if data.supplier.id is None:
                raise TransactionDomainError("Fornecedor informado é inválido.")
            supplier_id = data.supplier.id

        entity = FinancialTransactionEntity(
            tenant_id=data.tenant_id,
            bank_account_id=bank_account_id,
            installment_id=data.installment_id,
            type=data.type,
            category_id=category_id,
            cost_center_id=cost_center_id,
            supplier_id=supplier_id,
            amount=data.amount,
            description=data.description,
            reference_date=data.reference_date,
            due_date=data.due_date,
            payment_date=payment_date,
            status=status,
            document_number=data.document_number,
        )
        return entity

    @classmethod
    def update(
        cls,
        transaction: FinancialTransactionEntity,
        data: FinancialTransactionUpdateInput,
    ) -> FinancialTransactionEntity:
        updates = data.model_dump(exclude_unset=True)
        payload = transaction.model_dump()

        category = updates.pop("category", None)
        cost_center = updates.pop("cost_center", None)
        supplier = updates.pop("supplier", None)

        if category is not None:
            cls._ensure_tenant_match(transaction.tenant_id, category.tenant_id)
            cls._ensure_category_matches_type(transaction.type, category)
            payload["category_id"] = category.id

        if cost_center is not None:
            cls._ensure_tenant_match(transaction.tenant_id, cost_center.tenant_id)
            payload["cost_center_id"] = cost_center.id

        if supplier is not None:
            cls._ensure_tenant_match(transaction.tenant_id, supplier.tenant_id)
            if transaction.type != TransactionType.EXPENSE:
                raise TransactionDomainError("Fornecedor só pode ser associado a despesas.")
            payload["supplier_id"] = supplier.id

        for key, value in updates.items():
            if key == "payment_date" and value and payload.get("status") != TransactionStatus.PAID:
                payload["status"] = TransactionStatus.PAID
            payload[key] = value

        return FinancialTransactionEntity(**payload)

    @staticmethod
    def _ensure_tenant_consistency(data: FinancialTransactionCreateInput) -> None:
        tenant_id = data.tenant_id
        FinancialTransactionService._ensure_tenant_match(tenant_id, data.bank_account.tenant_id)
        FinancialTransactionService._ensure_tenant_match(tenant_id, data.category.tenant_id)

        if data.cost_center is not None:
            FinancialTransactionService._ensure_tenant_match(tenant_id, data.cost_center.tenant_id)
        if data.supplier is not None:
            FinancialTransactionService._ensure_tenant_match(tenant_id, data.supplier.tenant_id)

    @staticmethod
    def _ensure_tenant_match(expected: UUID, received: UUID) -> None:
        if expected != received:
            raise TenantMismatchError("Entidades relacionadas devem pertencer ao mesmo tenant.")

    @staticmethod
    def _ensure_category_matches_type(transaction_type: TransactionType, category: PaymentCategoryEntity) -> None:
        if category.type == PaymentCategoryType.BOTH:
            return
        if category.type == PaymentCategoryType.INCOME and transaction_type != TransactionType.INCOME:
            raise CategoryTypeMismatchError("Categoria de receita não pode ser usada em despesa.")
        if category.type == PaymentCategoryType.EXPENSE and transaction_type != TransactionType.EXPENSE:
            raise CategoryTypeMismatchError("Categoria de despesa não pode ser usada em receita.")


__all__ = [
    "BankAccountAlreadyExistsError",
    "BankAccountCreateInput",
    "BankAccountService",
    "BankAccountUpdateInput",
    "CategoryTypeMismatchError",
    "CostCenterAlreadyExistsError",
    "CostCenterCreateInput",
    "CostCenterService",
    "CostCenterUpdateInput",
    "FinanceDomainError",
    "FinancialTransactionCreateInput",
    "FinancialTransactionService",
    "FinancialTransactionUpdateInput",
    "MainBankAccountConflictError",
    "PaymentCategoryAlreadyExistsError",
    "PaymentCategoryCreateInput",
    "PaymentCategoryService",
    "PaymentCategoryUpdateInput",
    "SupplierAlreadyExistsError",
    "SupplierCreateInput",
    "SupplierService",
    "SupplierUpdateInput",
    "TenantMismatchError",
    "TransactionDomainError",
]
