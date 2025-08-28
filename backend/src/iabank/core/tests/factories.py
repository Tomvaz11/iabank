"""
Factories para os modelos do app core usando factory-boy.

Este módulo implementa as factories obrigatórias conforme Blueprint Diretriz 15,
garantindo a criação consistente de dados de teste com propagação correta
de tenant para isolamento multi-tenant.
"""

import factory
from django.contrib.auth import get_user_model

from ..models import Tenant

User = get_user_model()


class TenantFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo Tenant."""
    
    class Meta:
        model = Tenant
        django_get_or_create = ('name',)

    name = factory.Faker('company')
    is_active = True


class UserFactory(factory.django.DjangoModelFactory):
    """Factory para o modelo User customizado."""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    
    # CRÍTICO: Tenant é obrigatório conforme Blueprint
    tenant = factory.SubFactory(TenantFactory)


class AdminUserFactory(UserFactory):
    """Factory para usuário administrador."""
    
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f'admin{n}')