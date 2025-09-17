"""Testes do modelo Tenant com regras de multi-tenant."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from iabank.core.factories import generate_cnpj
from iabank.core.models import Tenant


def format_cnpj(digits: str) -> str:
    """Aplica formatacao padrao a um CNPJ de 14 digitos."""
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


class TenantModelTests(TestCase):
    """Validacoes essenciais do modelo Tenant."""

    def test_save_define_tenant_id_como_id(self):
        """Salvar Tenant deve definir tenant_id igual ao id do proprio tenant."""
        document = generate_cnpj()
        tenant = Tenant.objects.create(
            name="Empresa Teste",
            document=document,
        )

        self.assertEqual(tenant.id, tenant.tenant_id)

    def test_documento_formatado_e_normalizado(self):
        """Documento deve ser armazenado apenas com digitos apos validacao de CNPJ."""
        digits = generate_cnpj()
        formatted = format_cnpj(digits)
        tenant = Tenant.objects.create(
            name="Empresa Formatada",
            document=formatted,
        )

        self.assertEqual(tenant.document, digits)

    def test_documento_invalido_dispara_erro(self):
        """CNPJ invalido precisa disparar ValidationError."""
        with self.assertRaises(ValidationError):
            Tenant.objects.create(
                name="Empresa Invalida",
                document="11.111.111/1111-11",
            )

    def test_slug_gerado_automaticamente(self):
        """Slug deve ser gerado automaticamente a partir do nome quando ausente."""
        tenant = Tenant.objects.create(
            name="Empresa Com Slug",
            document=generate_cnpj(),
        )

        self.assertTrue(tenant.slug.startswith("empresa-com-slug"))

    def test_domain_unico(self):
        """Domain opcional deve ser unico quando informado."""
        Tenant.objects.create(
            name="Tenant Dominio",
            document=generate_cnpj(),
            domain="tenant.example.com",
        )

        with self.assertRaises((ValidationError, IntegrityError)):
            Tenant.objects.create(
                name="Tenant Dominio Duplicado",
                document=generate_cnpj(),
                domain="tenant.example.com",
            )
