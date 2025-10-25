from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from backend.apps.foundation.models import DesignSystemStory
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class DesignSystemStoryModelTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug='tenant-ds',
            display_name='Tenant DS',
            primary_domain='ds.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )
        with use_tenant(self.tenant.id):
            self.theme_token = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.SEMANTIC,
                json_payload={'surface.background': '#ffffff'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

    def test_allows_story_without_tenant_for_default_theme(self) -> None:
        story = DesignSystemStory(
            component_id='shared/ui/button',
            story_id='Primary',
            chromatic_build='build-123',
            coverage_percent=Decimal('98.5'),
            axe_status=DesignSystemStory.AxeStatus.PASS,
            axe_results={'violations': []},
            storybook_url='https://chromatic.example.com/story',
            theme_token=self.theme_token,
        )

        story.full_clean()
        story.save()

        self.assertIsNone(story.tenant)
        self.assertEqual(story.theme_token, self.theme_token)

    def test_rejects_coverage_percent_above_limit(self) -> None:
        story = DesignSystemStory(
            component_id='shared/ui/card',
            story_id='Overview',
            chromatic_build='build-999',
            coverage_percent=Decimal('120'),
            axe_status=DesignSystemStory.AxeStatus.WARN,
            axe_results={'violations': []},
            storybook_url='https://chromatic.example.com/story',
            tenant=self.tenant,
            theme_token=self.theme_token,
        )

        with self.assertRaises(ValidationError):
            story.full_clean()

    def test_rejects_invalid_axe_status(self) -> None:
        story = DesignSystemStory(
            component_id='shared/ui/modal',
            story_id='Default',
            chromatic_build='build-321',
            coverage_percent=Decimal('96.0'),
            axe_status='unknown',
            axe_results={'violations': []},
            storybook_url='https://chromatic.example.com/story',
            tenant=self.tenant,
            theme_token=self.theme_token,
        )

        with self.assertRaises(ValidationError):
            story.full_clean()
