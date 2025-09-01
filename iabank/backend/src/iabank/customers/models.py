"""
Modelos de dados do app Customers.

Define as entidades relacionadas aos clientes do sistema, incluindo
informações pessoais, endereços e outros dados necessários para
a gestão completa dos clientes.
"""

from django.db import models
from iabank.core.models import BaseTenantModel


class Customer(BaseTenantModel):
    """
    Modelo que representa um cliente no sistema.
    
    Contém informações pessoais, documentos, contatos e endereço
    necessários para a gestão de empréstimos.
    """
    
    # Informações pessoais
    name = models.CharField(max_length=255, verbose_name="Nome completo")
    document_number = models.CharField(
        max_length=20,
        verbose_name="CPF/CNPJ",
        help_text="Documento de identificação único"
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de nascimento")
    
    # Contatos
    email = models.EmailField(null=True, blank=True, verbose_name="E-mail")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Telefone")
    mobile_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Celular")
    
    # Endereço
    zip_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="CEP")
    street = models.CharField(max_length=255, null=True, blank=True, verbose_name="Rua")
    number = models.CharField(max_length=20, null=True, blank=True, verbose_name="Número")
    complement = models.CharField(max_length=100, null=True, blank=True, verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, null=True, blank=True, verbose_name="Bairro")
    city = models.CharField(max_length=100, null=True, blank=True, verbose_name="Cidade")
    state = models.CharField(max_length=2, null=True, blank=True, verbose_name="Estado")
    
    # Metadados
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    notes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        unique_together = [['tenant', 'document_number']]
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.document_number})"

    @property
    def full_address(self):
        """Retorna o endereço completo formatado."""
        address_parts = [
            self.street,
            self.number,
            self.complement,
            self.neighborhood,
            self.city,
            self.state,
            self.zip_code
        ]
        return ", ".join(filter(None, address_parts))

    @property
    def primary_contact(self):
        """Retorna o contato principal (celular ou telefone)."""
        return self.mobile_phone or self.phone