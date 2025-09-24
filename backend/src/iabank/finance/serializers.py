"""Serializers para o módulo financeiro do IABANK."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from iabank.finance.domain.entities import (
    BankAccountEntity,
    CostCenterEntity,
    FinancialTransactionEntity,
    PaymentCategoryEntity,
    SupplierEntity,
    TransactionStatus as DomainTransactionStatus,
    TransactionType as DomainTransactionType,
)
from iabank.finance.domain.services import (
    BankAccountAlreadyExistsError,
    BankAccountCreateInput,
    BankAccountService,
    BankAccountUpdateInput,
    CategoryTypeMismatchError,
    CostCenterAlreadyExistsError,
    CostCenterCreateInput,
    CostCenterService,
    CostCenterUpdateInput,
    FinanceDomainError,
    FinancialTransactionCreateInput,
    FinancialTransactionService,
    FinancialTransactionUpdateInput,
    MainBankAccountConflictError,
    PaymentCategoryAlreadyExistsError,
    PaymentCategoryCreateInput,
    PaymentCategoryService,
    PaymentCategoryUpdateInput,
    SupplierAlreadyExistsError,
    SupplierCreateInput,
    SupplierService,
    SupplierUpdateInput,
    TenantMismatchError,
    TransactionDomainError,
)
from iabank.finance.models import (
    BankAccount,
    CostCenter,
    FinancialTransaction,
    PaymentCategory,
    Supplier,
    TransactionStatus as ModelTransactionStatus,
    TransactionType as ModelTransactionType,
)
from iabank.operations.models import Installment


def _map_pydantic_errors(exc: PydanticValidationError) -> Dict[str, List[str]]:
    """Converte erros do Pydantic para formato do DRF."""

    errors: Dict[str, List[str]] = {}
    for error in exc.errors():
        loc = error.get("loc") or ("non_field_errors",)
        field = str(loc[-1]) if loc else "non_field_errors"
        errors.setdefault(field, []).append(str(error.get("msg")))
    return errors


def _map_integrity_error(exc: IntegrityError) -> Dict[str, List[str]]:
    """Mapeia violações de integridade conhecidas para mensagens amigáveis."""

    message = str(exc)
    if "fin_bank_unique_account_per_tenant" in message:
        return {"account_number": ["Conta bancária já cadastrada para este tenant."]}
    if "fin_bank_unique_main_per_tenant" in message:
        return {"is_main": ["Já existe uma conta principal cadastrada para este tenant."]}
    if "fin_paycat_unique_name_per_tenant" in message:
        return {"name": ["Categoria com este nome já existe no tenant."]}
    if "fin_cost_center_unique_code" in message:
        return {"code": ["Código já utilizado por outro centro de custo."]}
    if "fin_supplier_unique_document" in message:
        return {"document": ["Fornecedor com este documento já existe no tenant."]}
    return {"non_field_errors": ["Violação de integridade de dados."]}


def _coerce_enum(value: Any) -> Any:
    """Extrai valor de enums StrEnum mantendo strings simples."""

    return getattr(value, "value", value)


def _convert_model_to_bank_entity(instance: BankAccount) -> BankAccountEntity:
    """Converte modelo ORM em entidade de domínio de conta bancária."""

    return BankAccountEntity.model_validate(instance)


def _convert_model_to_category(instance: PaymentCategory) -> PaymentCategoryEntity:
    return PaymentCategoryEntity.model_validate(instance)


def _convert_model_to_cost_center(instance: CostCenter) -> CostCenterEntity:
    return CostCenterEntity.model_validate(instance)


def _convert_model_to_supplier(instance: Supplier) -> SupplierEntity:
    return SupplierEntity.model_validate(instance)


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer para criação e atualização de contas bancárias."""

    tenant_id = serializers.UUIDField(read_only=True)
    balance = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BankAccount
        fields = (
            "id",
            "tenant_id",
            "bank_code",
            "bank_name",
            "agency",
            "account_number",
            "account_type",
            "balance",
            "is_active",
            "is_main",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tenant_id", "balance", "created_at", "updated_at")
        extra_kwargs = {
            "bank_name": {"required": False, "allow_blank": True},
            "is_active": {"required": False},
            "is_main": {"required": False},
        }

    def create(self, validated_data: Dict[str, Any]) -> BankAccount:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Contexto da requisição é obrigatório."]})

        tenant_id = self.context.get("tenant_id") or getattr(request, "tenant_id", None) or getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            raise DRFValidationError({"detail": ["Tenant não identificado na requisição."]})
        tenant_uuid = UUID(str(tenant_id))

        input_payload = BankAccountCreateInput(tenant_id=tenant_uuid, **validated_data)
        existing = BankAccount.objects.filter(tenant_id=tenant_uuid)

        try:
            entity = BankAccountService.create(input_payload, existing_accounts=existing)
        except (FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance = BankAccount(
            tenant_id=entity.tenant_id,
            bank_code=entity.bank_code,
            bank_name=entity.bank_name or "",
            agency=entity.agency,
            account_number=entity.account_number,
            account_type=_coerce_enum(entity.account_type),
            balance=entity.balance,
            is_active=entity.is_active,
            is_main=entity.is_main,
            account_identifier_hash=entity.account_identifier_hash,
        )

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc

        return instance

    def update(self, instance: BankAccount, validated_data: Dict[str, Any]) -> BankAccount:
        entity = _convert_model_to_bank_entity(instance)
        input_payload = BankAccountUpdateInput(**validated_data)
        existing = BankAccount.objects.filter(tenant_id=instance.tenant_id).exclude(id=instance.id)

        try:
            updated_entity = BankAccountService.update(
                entity,
                input_payload,
                existing_accounts=existing,
            )
        except (FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance.bank_code = updated_entity.bank_code
        instance.bank_name = updated_entity.bank_name or ""
        instance.agency = updated_entity.agency
        instance.account_number = updated_entity.account_number
        instance.account_type = _coerce_enum(updated_entity.account_type)
        instance.is_active = updated_entity.is_active
        instance.is_main = updated_entity.is_main
        instance.account_identifier_hash = updated_entity.account_identifier_hash

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc

        return instance


class PaymentCategorySerializer(serializers.ModelSerializer):
    """Serializer para categorias de pagamento."""

    tenant_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = PaymentCategory
        fields = (
            "id",
            "tenant_id",
            "name",
            "type",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")

    def create(self, validated_data: Dict[str, Any]) -> PaymentCategory:
        tenant_uuid = self._resolve_tenant_uuid()
        input_payload = PaymentCategoryCreateInput(tenant_id=tenant_uuid, **validated_data)
        existing = PaymentCategory.objects.filter(tenant_id=tenant_uuid)

        try:
            entity = PaymentCategoryService.create(input_payload, existing_categories=existing)
        except (PaymentCategoryAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance = PaymentCategory(
            tenant_id=entity.tenant_id,
            name=entity.name,
            type=_coerce_enum(entity.type),
            is_active=entity.is_active,
        )
        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def update(self, instance: PaymentCategory, validated_data: Dict[str, Any]) -> PaymentCategory:
        entity = _convert_model_to_category(instance)
        input_payload = PaymentCategoryUpdateInput(**validated_data)
        existing = PaymentCategory.objects.filter(tenant_id=instance.tenant_id).exclude(id=instance.id)

        try:
            updated = PaymentCategoryService.update(entity, input_payload, existing_categories=existing)
        except (PaymentCategoryAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance.name = updated.name
        instance.type = _coerce_enum(updated.type)
        instance.is_active = updated.is_active

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def _resolve_tenant_uuid(self) -> UUID:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Contexto da requisição é obrigatório."]})
        tenant_id = self.context.get("tenant_id") or getattr(request, "tenant_id", None) or getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            raise DRFValidationError({"detail": ["Tenant não identificado na requisição."]})
        return UUID(str(tenant_id))


class CostCenterSerializer(serializers.ModelSerializer):
    """Serializer para centros de custo."""

    tenant_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CostCenter
        fields = (
            "id",
            "tenant_id",
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")

    def create(self, validated_data: Dict[str, Any]) -> CostCenter:
        tenant_uuid = self._resolve_tenant_uuid()
        input_payload = CostCenterCreateInput(tenant_id=tenant_uuid, **validated_data)
        existing = CostCenter.objects.filter(tenant_id=tenant_uuid)

        try:
            entity = CostCenterService.create(input_payload, existing_centers=existing)
        except (CostCenterAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance = CostCenter(
            tenant_id=entity.tenant_id,
            code=entity.code,
            name=entity.name,
            description=entity.description or "",
            is_active=entity.is_active,
        )
        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def update(self, instance: CostCenter, validated_data: Dict[str, Any]) -> CostCenter:
        entity = _convert_model_to_cost_center(instance)
        input_payload = CostCenterUpdateInput(**validated_data)
        existing = CostCenter.objects.filter(tenant_id=instance.tenant_id).exclude(id=instance.id)

        try:
            updated = CostCenterService.update(entity, input_payload, existing_centers=existing)
        except (CostCenterAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance.code = updated.code
        instance.name = updated.name
        instance.description = updated.description or ""
        instance.is_active = updated.is_active

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def _resolve_tenant_uuid(self) -> UUID:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Contexto da requisição é obrigatório."]})
        tenant_id = self.context.get("tenant_id") or getattr(request, "tenant_id", None) or getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            raise DRFValidationError({"detail": ["Tenant não identificado na requisição."]})
        return UUID(str(tenant_id))


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para fornecedores."""

    tenant_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Supplier
        fields = (
            "id",
            "tenant_id",
            "document_type",
            "document",
            "name",
            "email",
            "phone",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")

    def create(self, validated_data: Dict[str, Any]) -> Supplier:
        tenant_uuid = self._resolve_tenant_uuid()
        input_payload = SupplierCreateInput(tenant_id=tenant_uuid, **validated_data)
        existing = Supplier.objects.filter(tenant_id=tenant_uuid)

        try:
            entity = SupplierService.create(input_payload, existing_suppliers=existing)
        except (SupplierAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance = Supplier(
            tenant_id=entity.tenant_id,
            document_type=_coerce_enum(entity.document_type),
            document=entity.document,
            document_hash=entity.document_hash,
            name=entity.name,
            email=entity.email or "",
            phone=entity.phone or "",
            is_active=entity.is_active,
        )
        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def update(self, instance: Supplier, validated_data: Dict[str, Any]) -> Supplier:
        entity = _convert_model_to_supplier(instance)
        input_payload = SupplierUpdateInput(**validated_data)
        existing = Supplier.objects.filter(tenant_id=instance.tenant_id).exclude(id=instance.id)

        try:
            updated = SupplierService.update(entity, input_payload, existing_suppliers=existing)
        except (SupplierAlreadyExistsError, FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance.document_type = _coerce_enum(updated.document_type)
        instance.document = updated.document
        instance.document_hash = updated.document_hash
        instance.name = updated.name
        instance.email = updated.email or ""
        instance.phone = updated.phone or ""
        instance.is_active = updated.is_active

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc
        return instance

    def _resolve_tenant_uuid(self) -> UUID:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Contexto da requisição é obrigatório."]})
        tenant_id = self.context.get("tenant_id") or getattr(request, "tenant_id", None) or getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            raise DRFValidationError({"detail": ["Tenant não identificado na requisição."]})
        return UUID(str(tenant_id))


class FinancialTransactionOutputSerializer(serializers.ModelSerializer):
    """Serializer de leitura para transações financeiras."""

    tenant_id = serializers.UUIDField(read_only=True)
    bank_account_id = serializers.UUIDField(source="bank_account.id", read_only=True)
    category_id = serializers.UUIDField(source="category.id", read_only=True)
    cost_center_id = serializers.UUIDField(source="cost_center.id", read_only=True)
    supplier_id = serializers.UUIDField(source="supplier.id", read_only=True)
    installment_id = serializers.UUIDField(source="installment.id", read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "tenant_id",
            "bank_account_id",
            "installment_id",
            "type",
            "category_id",
            "cost_center_id",
            "supplier_id",
            "amount",
            "description",
            "reference_date",
            "due_date",
            "payment_date",
            "status",
            "document_number",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class FinancialTransactionSerializer(serializers.ModelSerializer):
    """Serializer principal para criação/atualização de transações."""

    tenant_id = serializers.UUIDField(read_only=True)
    bank_account_id = serializers.UUIDField(write_only=True)
    category_id = serializers.UUIDField(write_only=True)
    cost_center_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    supplier_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    installment_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "tenant_id",
            "bank_account_id",
            "installment_id",
            "type",
            "category_id",
            "cost_center_id",
            "supplier_id",
            "amount",
            "description",
            "reference_date",
            "due_date",
            "payment_date",
            "status",
            "document_number",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "tenant_id", "created_at", "updated_at")
        extra_kwargs = {
            "document_number": {"required": False, "allow_blank": True},
            "due_date": {"required": False, "allow_null": True},
            "payment_date": {"required": False, "allow_null": True},
            "status": {"required": False, "default": ModelTransactionStatus.PENDING},
        }

    def create(self, validated_data: Dict[str, Any]) -> FinancialTransaction:
        tenant_uuid = self._resolve_tenant_uuid()
        bank_account = self._get_bank_account(tenant_uuid, validated_data.pop("bank_account_id"))
        category = self._get_category(tenant_uuid, validated_data.pop("category_id"))
        cost_center = self._get_cost_center(tenant_uuid, validated_data.pop("cost_center_id", None))
        supplier = self._get_supplier(tenant_uuid, validated_data.pop("supplier_id", None))
        installment = self._get_installment(tenant_uuid, validated_data.pop("installment_id", None))

        status_value = validated_data.get("status") or ModelTransactionStatus.PENDING
        domain_status = DomainTransactionStatus(str(status_value))
        domain_type = DomainTransactionType(str(validated_data["type"]))

        domain_input = FinancialTransactionCreateInput(
            tenant_id=tenant_uuid,
            bank_account=BankAccountEntity.model_validate(bank_account),
            category=PaymentCategoryEntity.model_validate(category),
            type=domain_type,
            amount=validated_data["amount"],
            description=validated_data["description"],
            reference_date=validated_data["reference_date"],
            status=domain_status,
            cost_center=CostCenterEntity.model_validate(cost_center) if cost_center else None,
            supplier=SupplierEntity.model_validate(supplier) if supplier else None,
            installment_id=installment.id if installment else None,
            due_date=validated_data.get("due_date"),
            payment_date=validated_data.get("payment_date"),
            document_number=validated_data.get("document_number"),
        )

        try:
            entity = FinancialTransactionService.create(domain_input)
        except (FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance = FinancialTransaction(
            tenant_id=tenant_uuid,
            bank_account=bank_account,
            installment=installment,
            type=_coerce_enum(entity.type),
            category=category,
            cost_center=cost_center,
            supplier=supplier,
            amount=entity.amount,
            description=entity.description,
            reference_date=entity.reference_date,
            due_date=entity.due_date,
            payment_date=entity.payment_date,
            status=_coerce_enum(entity.status),
            document_number=entity.document_number or "",
        )

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc

        return instance

    def update(self, instance: FinancialTransaction, validated_data: Dict[str, Any]) -> FinancialTransaction:
        entity = FinancialTransactionEntity.model_validate(instance)

        category = None
        if "category_id" in validated_data:
            category = self._get_category(instance.tenant_id, validated_data.pop("category_id"))

        cost_center = None
        if "cost_center_id" in validated_data:
            cost_center = self._get_cost_center(instance.tenant_id, validated_data.pop("cost_center_id"))

        supplier = None
        if "supplier_id" in validated_data:
            supplier = self._get_supplier(instance.tenant_id, validated_data.pop("supplier_id"))

        if "bank_account_id" in validated_data:
            raise DRFValidationError({"bank_account_id": ["Conta bancária não pode ser alterada."]})

        domain_input = FinancialTransactionUpdateInput(
            description=validated_data.get("description"),
            status=DomainTransactionStatus(str(validated_data.get("status", instance.status))),
            payment_date=validated_data.get("payment_date"),
            document_number=validated_data.get("document_number"),
            cost_center=CostCenterEntity.model_validate(cost_center) if cost_center else None,
            supplier=SupplierEntity.model_validate(supplier) if supplier else None,
            category=PaymentCategoryEntity.model_validate(category) if category else None,
        )

        try:
            updated_entity = FinancialTransactionService.update(entity, domain_input)
        except (FinanceDomainError, PydanticValidationError) as exc:
            if isinstance(exc, PydanticValidationError):
                raise DRFValidationError(_map_pydantic_errors(exc)) from exc
            raise DRFValidationError({"detail": [str(exc)]}) from exc

        instance.category = category or instance.category
        instance.cost_center = cost_center or instance.cost_center
        instance.supplier = supplier or instance.supplier
        instance.description = updated_entity.description
        instance.status = _coerce_enum(updated_entity.status)
        instance.payment_date = updated_entity.payment_date
        instance.document_number = updated_entity.document_number or ""

        try:
            instance.full_clean()
            instance.save()
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict) from exc
        except IntegrityError as exc:
            raise DRFValidationError(_map_integrity_error(exc)) from exc

        return instance

    def _resolve_tenant_uuid(self) -> UUID:
        request = self.context.get("request")
        if request is None:
            raise DRFValidationError({"detail": ["Contexto da requisição é obrigatório."]})
        tenant_id = self.context.get("tenant_id") or getattr(request, "tenant_id", None) or getattr(request.user, "tenant_id", None)
        if tenant_id is None:
            raise DRFValidationError({"detail": ["Tenant não identificado na requisição."]})
        return UUID(str(tenant_id))

    def _get_bank_account(self, tenant_id: UUID, pk: UUID) -> BankAccount:
        try:
            account = BankAccount.objects.get(id=pk, tenant_id=tenant_id)
        except BankAccount.DoesNotExist as exc:
            raise DRFValidationError({"bank_account_id": ["Conta bancária não encontrada para este tenant."]}) from exc
        return account

    def _get_category(self, tenant_id: UUID, pk: UUID) -> PaymentCategory:
        try:
            category = PaymentCategory.objects.get(id=pk, tenant_id=tenant_id)
        except PaymentCategory.DoesNotExist as exc:
            raise DRFValidationError({"category_id": ["Categoria não encontrada para este tenant."]}) from exc
        return category

    def _get_cost_center(self, tenant_id: UUID, pk: Optional[UUID]) -> Optional[CostCenter]:
        if pk is None:
            return None
        try:
            return CostCenter.objects.get(id=pk, tenant_id=tenant_id)
        except CostCenter.DoesNotExist as exc:
            raise DRFValidationError({"cost_center_id": ["Centro de custo não encontrado para este tenant."]}) from exc

    def _get_supplier(self, tenant_id: UUID, pk: Optional[UUID]) -> Optional[Supplier]:
        if pk is None:
            return None
        try:
            return Supplier.objects.get(id=pk, tenant_id=tenant_id)
        except Supplier.DoesNotExist as exc:
            raise DRFValidationError({"supplier_id": ["Fornecedor não encontrado para este tenant."]}) from exc

    def _get_installment(self, tenant_id: UUID, pk: Optional[UUID]) -> Optional[Installment]:
        if pk is None:
            return None
        try:
            return Installment.objects.get(id=pk, tenant_id=tenant_id)
        except Installment.DoesNotExist as exc:
            raise DRFValidationError({"installment_id": ["Parcela não encontrada para este tenant."]}) from exc


__all__ = [
    "BankAccountSerializer",
    "CostCenterSerializer",
    "FinancialTransactionOutputSerializer",
    "FinancialTransactionSerializer",
    "PaymentCategorySerializer",
    "SupplierSerializer",
]
