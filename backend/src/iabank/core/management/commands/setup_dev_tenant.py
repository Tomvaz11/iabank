"""
Django management command to create a development tenant.
This command helps setup initial tenant data for development.
"""

import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from iabank.core.models import Tenant


class Command(BaseCommand):
    help = "Create a development tenant for testing multi-tenancy setup"

    def add_arguments(self, parser):
        parser.add_argument(
            "--name",
            type=str,
            default="Empresa de Desenvolvimento",
            help='Tenant company name (default: "Empresa de Desenvolvimento")',
        )
        parser.add_argument(
            "--slug",
            type=str,
            default="dev-company",
            help='Tenant slug (default: "dev-company")',
        )
        parser.add_argument(
            "--cnpj",
            type=str,
            default="11.222.333/0001-44",
            help='Company CNPJ (default: "11.222.333/0001-44")',
        )
        parser.add_argument(
            "--email",
            type=str,
            default="dev@iabank.local",
            help='Contact email (default: "dev@iabank.local")',
        )
        parser.add_argument(
            "--tenant-id", type=str, help="Specific UUID for tenant (optional)"
        )
        parser.add_argument(
            "--force", action="store_true", help="Force creation even if tenant exists"
        )

    def handle(self, *args, **options):
        name = options["name"]
        slug = options["slug"]
        cnpj = options["cnpj"]
        email = options["email"]
        tenant_id = options.get("tenant_id")
        force = options["force"]

        # Validate UUID if provided
        if tenant_id:
            try:
                tenant_id = uuid.UUID(tenant_id)
            except ValueError:
                raise CommandError(f"Invalid UUID format: {tenant_id}")

        # Check if tenant already exists
        existing_tenant = None
        if tenant_id:
            try:
                existing_tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                pass
        else:
            try:
                existing_tenant = Tenant.objects.get(slug=slug)
            except Tenant.DoesNotExist:
                pass

        if existing_tenant and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Tenant already exists: {existing_tenant.name} ({existing_tenant.id})"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Use --force to recreate or use existing tenant ID: {existing_tenant.id}"
                )
            )
            return

        # Delete existing tenant if force is used
        if existing_tenant and force:
            existing_tenant.delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted existing tenant: {existing_tenant.name}")
            )

        # Create new tenant
        try:
            with transaction.atomic():
                tenant_data = {
                    "name": name,
                    "slug": slug,
                    "cnpj": cnpj,
                    "email": email,
                    "is_active": True,
                    "subscription_plan": "ENTERPRISE",  # Development uses enterprise features
                    "max_users": 50,
                    "max_loans_per_month": 1000,
                    "address": "Rua do Desenvolvimento, 123",
                    "city": "São Paulo",
                    "state": "SP",
                    "zip_code": "01234-567",
                    "phone": "(11) 99999-9999",
                    "max_interest_rate": 12.00,
                }

                if tenant_id:
                    tenant_data["id"] = tenant_id

                tenant = Tenant.objects.create(**tenant_data)

                self.stdout.write(
                    self.style.SUCCESS("Development tenant created successfully!")
                )
                self.stdout.write(f"   ID: {tenant.id}")
                self.stdout.write(f"   Name: {tenant.name}")
                self.stdout.write(f"   CNPJ: {tenant.cnpj}")
                self.stdout.write(f"   Slug: {tenant.slug}")
                self.stdout.write(f"   Email: {tenant.email}")
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS("Add this to your .env file:"))
                self.stdout.write(f"DEFAULT_TENANT_ID={tenant.id}")
                self.stdout.write("")
                self.stdout.write(
                    self.style.SUCCESS("Or use this tenant ID in API headers:")
                )
                self.stdout.write(f"X-Tenant-ID: {tenant.id}")

        except Exception as e:
            raise CommandError(f"Error creating tenant: {e}")
