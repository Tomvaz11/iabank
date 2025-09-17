"""
Factories base para IABANK com tenant propagation automática.
Garante isolamento de dados em todos os testes.
"""
import random
import uuid
from typing import Any, Dict, Optional

import factory
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from factory import fuzzy

from iabank.core.models import BaseTenantModel, Tenant


User = get_user_model()



def generate_cnpj() -> str:
    """Gera um CNPJ valido para uso em testes."""
    numbers = [random.randint(0, 9) for _ in range(12)]

    def _calc_digit(sequence, weights):
        total = sum(d * w for d, w in zip(sequence, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first_digit = _calc_digit(numbers, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    numbers.append(first_digit)
    second_digit = _calc_digit(numbers, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    numbers.append(second_digit)

    return ''.join(str(n) for n in numbers)



def default_tenant_settings() -> Dict[str, Any]:
    """Retorna copia das configuracoes padrao do Tenant."""
    default = Tenant._meta.get_field('settings').default
    if callable(default):
        return default()
    return dict(default)



class TenantFactory(factory.django.DjangoModelFactory):
    """Factory para modelo Tenant com CNPJ valido e slug unico."""

    class Meta:
        model = Tenant

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda obj: slugify(f"{obj.name}-{uuid.uuid4().hex[:6]}"))
    document = factory.LazyFunction(generate_cnpj)
    domain = factory.LazyAttribute(lambda obj: f"{obj.slug}.iabank.dev")
    contact_email = factory.Faker("company_email")
    phone_number = factory.Faker("phone_number")
    is_active = True
    created_by = factory.Faker("user_name")
    settings = factory.LazyFunction(default_tenant_settings)

    @factory.lazy_attribute
    def tenant_id(self):
        """Auto-define tenant_id como proprio id."""
        return self.id

class BaseTenantFactory(factory.django.DjangoModelFactory):
    """
    Factory base para todos os models que herdam BaseTenantModel.

    Features:
    - Propagação automática de tenant_id
    - Contexto global de tenant para testes
    - Validação de isolamento
    """

    class Meta:
        abstract = True

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = factory.LazyAttribute(lambda obj: get_current_tenant_id())


# Context global para tenant nos testes
_current_tenant_context: Optional[uuid.UUID] = None


def get_current_tenant_id() -> uuid.UUID:
    """
    Retorna tenant_id do contexto atual.

    Returns:
        UUID: tenant_id ativo

    Raises:
        ValueError: Se contexto não definido
    """
    global _current_tenant_context
    if _current_tenant_context is None:
        # Cria tenant padrão se não há contexto
        tenant = TenantFactory()
        _current_tenant_context = tenant.id
        return tenant.id
    return _current_tenant_context


def set_tenant_context(tenant_id: Optional[uuid.UUID]):
    """
    Define contexto de tenant para factories.

    Args:
        tenant_id: ID do tenant ou None para limpar
    """
    global _current_tenant_context
    _current_tenant_context = tenant_id


def clear_tenant_context():
    """Limpa contexto de tenant."""
    global _current_tenant_context
    _current_tenant_context = None


class TenantContextManager:
    """
    Context manager para isolar tenant em testes.

    Usage:
        with TenantContextManager(tenant_id):
            # Todas as factories usarão este tenant_id
            customer = CustomerFactory()
    """

    def __init__(self, tenant_id: Optional[uuid.UUID] = None):
        self.tenant_id = tenant_id
        self.previous_context = None

    def __enter__(self):
        global _current_tenant_context
        self.previous_context = _current_tenant_context
        set_tenant_context(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        set_tenant_context(self.previous_context)


class TenantIsolatedFactory(BaseTenantFactory):
    """
    Factory com isolamento de tenant mais rigoroso.

    Features:
    - Validação obrigatória de tenant_id
    - Logging de criação para auditoria
    - Propagação para objetos relacionados
    """

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Override para validação e logging.

        Args:
            model_class: Classe do modelo
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Instance: Instância criada
        """
        # Garante tenant_id obrigatório
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = get_current_tenant_id()

        if not kwargs["tenant_id"]:
            raise ValueError(
                f"tenant_id obrigatório para {model_class.__name__} factory"
            )

        # Cria instância
        instance = super()._create(model_class, *args, **kwargs)

        # Log para auditoria de testes
        from iabank.core.logging import get_logger
        logger = get_logger(f"factory.{model_class.__name__}")
        logger.debug(
            "Factory instance created",
            model=model_class.__name__,
            instance_id=str(instance.id),
            tenant_id=str(instance.tenant_id),
        )

        return instance


class FactoryUtils:
    """
    Utilitários para factories e testes multi-tenant.

    Features:
    - Criação de datasets isolados
    - Validação de isolamento
    - Limpeza de dados de teste
    """

    @staticmethod
    def create_isolated_dataset(
        tenant_id: Optional[uuid.UUID] = None,
        factories: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Cria dataset isolado por tenant.

        Args:
            tenant_id: ID do tenant (cria novo se None)
            factories: Dict de factories para executar

        Returns:
            dict: Dataset criado com isolamento
        """
        if tenant_id is None:
            tenant = TenantFactory()
            tenant_id = tenant.id
        else:
            tenant = Tenant.objects.get(id=tenant_id)

        with TenantContextManager(tenant_id):
            dataset = {"tenant": tenant}

            if factories:
                for name, factory_config in factories.items():
                    if isinstance(factory_config, dict):
                        factory_class = factory_config.pop("factory")
                        count = factory_config.pop("count", 1)
                        kwargs = factory_config
                    else:
                        factory_class = factory_config
                        count = 1
                        kwargs = {}

                    if count == 1:
                        dataset[name] = factory_class(**kwargs)
                    else:
                        dataset[name] = factory_class.create_batch(count, **kwargs)

            return dataset

    @staticmethod
    def validate_tenant_isolation(
        instances: list,
        expected_tenant_id: uuid.UUID,
    ) -> bool:
        """
        Valida isolamento de tenant em instâncias.

        Args:
            instances: Lista de instâncias para validar
            expected_tenant_id: Tenant esperado

        Returns:
            bool: True se todas isoladas corretamente
        """
        for instance in instances:
            if isinstance(instance, BaseTenantModel):
                if instance.tenant_id != expected_tenant_id:
                    return False
            elif hasattr(instance, "tenant_id"):
                if instance.tenant_id != expected_tenant_id:
                    return False

        return True

    @staticmethod
    def cleanup_tenant_data(tenant_id: uuid.UUID):
        """
        Remove todos os dados de um tenant específico.

        Args:
            tenant_id: ID do tenant para limpar
        """
        from django.apps import apps

        # Encontra todos os models que herdam BaseTenantModel
        for model in apps.get_models():
            if (
                hasattr(model, "tenant_id")
                and hasattr(model, "_meta")
                and not model._meta.abstract
            ):
                try:
                    model.objects.filter(tenant_id=tenant_id).delete()
                except Exception:
                    # Ignora erros de constraint/FK
                    pass


# Exemplo de uso em factories específicas (será usado nos testes):

# class CustomerFactory(TenantIsolatedFactory):
#     class Meta:
#         model = Customer
#
#     name = factory.Faker("name")
#     email = factory.Faker("email")
#     phone = factory.Faker("phone_number")
#
# class LoanFactory(TenantIsolatedFactory):
#     class Meta:
#         model = Loan
#
#     customer = factory.SubFactory(CustomerFactory)
#     amount = fuzzy.FuzzyDecimal(1000, 50000, 2)
#     interest_rate = fuzzy.FuzzyDecimal(0.5, 3.0, 2)