"""Serializers para operações de clientes utilizando camada de domínio."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from iabank.customers.domain.entities import AddressEntity, CustomerEntity
from iabank.customers.domain.services import (
    AddressCreateInput,
    AddressUpdateInput,
    CustomerCreateInput,
    CustomerService,
    CustomerUpdateInput,
    DuplicatePrimaryAddressError,
    InvalidDocumentError,
)
from iabank.customers.models import (
    Address,
    AddressState,
    AddressType,
    Customer,
    CustomerDocumentType,
    CustomerGender,
)


def _map_pydantic_errors(exc: PydanticValidationError) -> Dict[str, List[str]]:
    """Converte erros do Pydantic para formato DRF."""

    errors: Dict[str, List[str]] = {}
    for error in exc.errors():
        loc = error.get("loc") or ("non_field_errors",)
        field = str(loc[-1]) if loc else "non_field_errors"
        errors.setdefault(field, []).append(str(error.get("msg")))
    return errors


def _map_integrity_error(exc: IntegrityError) -> Dict[str, List[str]]:
    """Mapeia erros de integridade conhecidos para mensagens amigáveis."""

    message = str(exc)
    if "cust_cust_doc_hash_uniq" in message:
        return {"document": ["Cliente com este documento já existe no tenant."]}
    if "cust_addr_primary_unique" in message:
        return {"addresses": ["Apenas um endereço pode ser marcado como principal."]}
    return {"non_field_errors": ["Violação de integridade de dados."]}


def _coerce_enum_value(value: Any) -> Any:
    """Extrai valor de enums StrEnum preservando strings simples."""

    return getattr(value, "value", value)


def _ensure_score_timestamp(entity: CustomerEntity) -> CustomerEntity:
    """Garante timestamp de score caso haja valor informado."""

    if entity.credit_score is not None and entity.score_last_updated is None:
        return entity.model_copy(update={"score_last_updated": timezone.now()})
    return entity


def _sync_customer_model(instance: Customer, entity: CustomerEntity) -> None:
    """Sincroniza dados de uma entidade de domínio com o modelo ORM."""

    instance.tenant_id = UUID(str(entity.tenant_id))
    instance.document_type = str(_coerce_enum_value(entity.document_type))
    instance.document = entity.document
    instance.document_hash = entity.document_hash or instance.document_hash
    instance.name = entity.name
    instance.email = entity.email
    instance.phone = entity.phone or ""
    instance.birth_date = entity.birth_date
    gender_value = _coerce_enum_value(entity.gender) if entity.gender else ""
    instance.gender = gender_value or ""
    instance.profession = entity.profession or ""
    instance.monthly_income = entity.monthly_income
    instance.credit_score = entity.credit_score
    instance.score_last_updated = entity.score_last_updated
    instance.is_active = entity.is_active


def _sync_addresses(customer: Customer, addresses: Iterable[AddressEntity]) -> None:
    """Atualiza endereços do cliente com base na entidade de domínio."""

    current_addresses = {
        str(address.id): address for address in customer.addresses.all()
    }
    desired_ids: set[str] = set()

    for address_entity in addresses:
        address_id = str(address_entity.id) if address_entity.id else None
        if address_id and address_id in current_addresses:
            model_address = current_addresses[address_id]
            model_address.type = str(_coerce_enum_value(address_entity.type))
            model_address.street = address_entity.street
            model_address.number = address_entity.number
            model_address.complement = address_entity.complement or ""
            model_address.neighborhood = address_entity.neighborhood
            model_address.city = address_entity.city
            model_address.state = address_entity.state
            model_address.zipcode = address_entity.zipcode
            model_address.is_primary = address_entity.is_primary
            model_address.full_clean()
            model_address.save()
            desired_ids.add(address_id)
        else:
            Address.objects.create(
                customer=customer,
                tenant_id=customer.tenant_id,
                type=str(_coerce_enum_value(address_entity.type)),
                street=address_entity.street,
                number=address_entity.number,
                complement=address_entity.complement or "",
                neighborhood=address_entity.neighborhood,
                city=address_entity.city,
                state=address_entity.state,
                zipcode=address_entity.zipcode,
                is_primary=address_entity.is_primary,
            )

    if current_addresses:
        for address_id, model_address in current_addresses.items():
            if address_id not in desired_ids:
                model_address.delete()


class AddressBaseSerializer(serializers.Serializer):
    """Campos compartilhados entre criação e atualização de endereços."""

    type = serializers.ChoiceField(choices=AddressType.choices, default=AddressType.RESIDENTIAL)
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=20)
    complement = serializers.CharField(max_length=100, required=False, allow_blank=True)
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.ChoiceField(choices=AddressState.choices)
    zipcode = serializers.CharField(max_length=9)
    is_primary = serializers.BooleanField(required=False, default=False)

    def validate_zipcode(self, value: str) -> str:
        digits = ''.join(filter(str.isdigit, value or ""))
        if len(digits) != 8:
            raise serializers.ValidationError("CEP deve conter 8 dígitos")
        return f"{digits[:5]}-{digits[5:]}"


class AddressCreateSerializer(AddressBaseSerializer):
    """Serializer para criação de endereços."""

    pass


class AddressUpdateSerializer(AddressBaseSerializer):
    """Serializer para atualização de endereços."""

    id = serializers.UUIDField(required=False)


class AddressOutputSerializer(serializers.ModelSerializer):
    """Serializer de leitura para endereços."""

    class Meta:
        model = Address
        fields = (
            "id",
            "type",
            "street",
            "number",
            "complement",
            "neighborhood",
            "city",
            "state",
            "zipcode",
            "is_primary",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CustomerOutputSerializer(serializers.ModelSerializer):
    """Serializer de resposta para clientes com endereços aninhados."""

    addresses = AddressOutputSerializer(many=True, read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Customer
        fields = (
            "id",
            "tenant_id",
            "document_type",
            "document",
            "name",
            "email",
            "phone",
            "birth_date",
            "gender",
            "profession",
            "monthly_income",
            "credit_score",
            "score_last_updated",
            "is_active",
            "created_at",
            "updated_at",
            "addresses",
        )
        read_only_fields = fields


class CustomerCreateSerializer(serializers.Serializer):
    """Serializer para criação de clientes via domínio."""

    document_type = serializers.ChoiceField(choices=CustomerDocumentType.choices)
    document = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=CustomerGender.choices, required=False)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True)
    monthly_income = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    credit_score = serializers.IntegerField(min_value=0, max_value=1000, required=False)
    addresses = AddressCreateSerializer(many=True, required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context.get("request")
        tenant_id = self._resolve_tenant_id(request)

        raw_addresses = attrs.get("addresses") or []

        try:
            address_inputs = [AddressCreateInput(**address) for address in raw_addresses]
            domain_input = CustomerCreateInput(
                tenant_id=tenant_id,
                document_type=attrs["document_type"],
                document=attrs["document"],
                name=attrs["name"],
                email=attrs["email"],
                phone=attrs.get("phone"),
                birth_date=attrs.get("birth_date"),
                gender=attrs.get("gender"),
                profession=attrs.get("profession"),
                monthly_income=attrs.get("monthly_income"),
                credit_score=attrs.get("credit_score"),
                addresses=address_inputs,
            )
        except PydanticValidationError as exc:
            raise serializers.ValidationError(_map_pydantic_errors(exc)) from exc
        except InvalidDocumentError as exc:
            raise serializers.ValidationError({"document": [str(exc)]}) from exc
        except DuplicatePrimaryAddressError as exc:
            raise serializers.ValidationError({"addresses": [str(exc)]}) from exc

        attrs["_domain_input"] = domain_input
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Customer:
        domain_input: CustomerCreateInput = validated_data.pop("_domain_input")

        try:
            entity = CustomerService.create_customer(domain_input)
            entity = _ensure_score_timestamp(entity)
        except DuplicatePrimaryAddressError as exc:
            raise serializers.ValidationError({"addresses": [str(exc)]}) from exc
        except PydanticValidationError as exc:
            raise serializers.ValidationError(_map_pydantic_errors(exc)) from exc

        try:
            return self._persist_entity(entity)
        except IntegrityError as exc:
            raise serializers.ValidationError(_map_integrity_error(exc)) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict or {"detail": [str(exc)]}) from exc

    def _persist_entity(self, entity: CustomerEntity) -> Customer:
        with transaction.atomic():
            customer = Customer()
            _sync_customer_model(customer, entity)
            if customer.credit_score is not None and customer.score_last_updated is None:
                customer.score_last_updated = timezone.now()
            customer.full_clean()
            customer.save()

            if entity.addresses:
                _sync_addresses(customer, entity.addresses)

            customer.refresh_from_db()
            return customer

    @staticmethod
    def _resolve_tenant_id(request) -> UUID:
        tenant_candidate = getattr(request, "tenant_id", None)
        if tenant_candidate is None and getattr(request, "user", None) is not None:
            tenant_candidate = getattr(request.user, "tenant_id", None)
        if tenant_candidate is None:
            raise serializers.ValidationError({"tenant": ["Tenant não identificado na requisição."]})
        try:
            return UUID(str(tenant_candidate))
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError({"tenant": ["Tenant inválido."]}) from exc


class CustomerUpdateSerializer(serializers.Serializer):
    """Serializer para atualização de clientes via domínio."""

    document_type = serializers.ChoiceField(choices=CustomerDocumentType.choices, required=False)
    document = serializers.CharField(max_length=32, required=False)
    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False)
    gender = serializers.ChoiceField(choices=CustomerGender.choices, required=False)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True)
    monthly_income = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    credit_score = serializers.IntegerField(min_value=0, max_value=1000, required=False)
    is_active = serializers.BooleanField(required=False)
    addresses = AddressUpdateSerializer(many=True, required=False)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        domain_payload = {key: value for key, value in attrs.items() if key not in {"is_active", "addresses"}}
        addresses_provided = "addresses" in attrs
        raw_addresses = attrs.get("addresses") or []

        try:
            domain_input = CustomerUpdateInput(**domain_payload)
            address_inputs = [AddressUpdateInput(**address) for address in raw_addresses]
        except PydanticValidationError as exc:
            raise serializers.ValidationError(_map_pydantic_errors(exc)) from exc
        except InvalidDocumentError as exc:
            raise serializers.ValidationError({"document": [str(exc)]}) from exc
        except DuplicatePrimaryAddressError as exc:
            raise serializers.ValidationError({"addresses": [str(exc)]}) from exc

        attrs["_domain_input"] = domain_input
        attrs["_addresses_input"] = address_inputs
        attrs["_addresses_provided"] = addresses_provided
        return attrs

    def update(self, instance: Customer, validated_data: Dict[str, Any]) -> Customer:
        domain_input: CustomerUpdateInput = validated_data.pop("_domain_input")
        address_inputs: List[AddressUpdateInput] = validated_data.pop("_addresses_input", [])
        addresses_provided: bool = validated_data.pop("_addresses_provided", False)
        is_active = validated_data.pop("is_active", None)

        current_entity = CustomerEntity.model_validate(instance)

        try:
            updated_entity = CustomerService.update_customer(current_entity, domain_input)
            if addresses_provided:
                updated_entity = CustomerService.replace_addresses(updated_entity, address_inputs)
            if is_active is True:
                updated_entity = CustomerService.activate(updated_entity)
            elif is_active is False:
                updated_entity = CustomerService.deactivate(updated_entity)
            updated_entity = _ensure_score_timestamp(updated_entity)
        except (InvalidDocumentError, DuplicatePrimaryAddressError) as exc:
            raise serializers.ValidationError({"detail": [str(exc)]}) from exc

        try:
            return self._persist_entity(instance, updated_entity, has_addresses=addresses_provided)
        except IntegrityError as exc:
            raise serializers.ValidationError(_map_integrity_error(exc)) from exc
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict or {"detail": [str(exc)]}) from exc

    def _persist_entity(
        self,
        instance: Customer,
        entity: CustomerEntity,
        *,
        has_addresses: bool,
    ) -> Customer:
        with transaction.atomic():
            _sync_customer_model(instance, entity)
            if instance.credit_score is not None and instance.score_last_updated is None:
                instance.score_last_updated = timezone.now()
            instance.full_clean()
            instance.save()

            if has_addresses:
                _sync_addresses(instance, entity.addresses)

            instance.refresh_from_db()
            return instance


class CreditAnalysisSerializer(serializers.Serializer):
    """Serializer para requisições de análise de crédito."""

    new_score = serializers.IntegerField(min_value=0, max_value=1000)
    analysis_reason = serializers.CharField(max_length=255, required=False, allow_blank=True)
    analyst_notes = serializers.CharField(required=False, allow_blank=True)
