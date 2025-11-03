from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from backend.apps.foundation.models import DesignSystemStory
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class DesignSystemStorySerializerTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug='tenant-serializer',
            display_name='Tenant Serializer',
            primary_domain='serializer.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )
        with use_tenant(self.tenant.id):
            self.theme_token = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary': '#123456'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

    def test_serializes_story_with_tenant_metadata(self) -> None:
        story = DesignSystemStory.objects.create(
            tenant=self.tenant,
            theme_token=self.theme_token,
            component_id='shared/ui/button',
            story_id='Primary',
            tags=['critical', 'button'],
            coverage_percent=Decimal('98.55'),
            axe_status=DesignSystemStory.AxeStatus.PASS,
            axe_results={'violations': [], 'passes': 12},
            chromatic_build='build-12345',
            storybook_url='https://chromatic.example.com/story',
        )

        from backend.apps.foundation.serializers.design_system_story import (
            DesignSystemStorySerializer,
        )

        data = DesignSystemStorySerializer(instance=story).data

        self.assertEqual(data['id'], str(story.id))
        self.assertEqual(data['tenantId'], str(self.tenant.id))
        self.assertEqual(data['componentId'], 'shared/ui/button')
        self.assertEqual(data['storyId'], 'Primary')
        self.assertEqual(data['tags'], ['critical', 'button'])
        self.assertEqual(data['axeStatus'], DesignSystemStory.AxeStatus.PASS)
        self.assertEqual(data['chromaticBuild'], 'build-12345')
        self.assertEqual(data['storybookUrl'], 'https://chromatic.example.com/story')
        self.assertAlmostEqual(data['coveragePercent'], float(Decimal('98.55')))
        self.assertIn('updatedAt', data)

    def test_serializes_story_without_tenant(self) -> None:
        story = DesignSystemStory.objects.create(
            tenant=None,
            theme_token=self.theme_token,
            component_id='shared/ui/card',
            story_id='Overview',
            tags=[],
            coverage_percent=Decimal('96.0'),
            axe_status=DesignSystemStory.AxeStatus.WARN,
            axe_results={'violations': [{'id': 'color-contrast'}]},
            chromatic_build='build-67890',
            storybook_url='https://chromatic.example.com/card',
        )

        from backend.apps.foundation.serializers.design_system_story import (
            DesignSystemStorySerializer,
        )

        data = DesignSystemStorySerializer(instance=story).data

        self.assertIsNone(data['tenantId'])
        self.assertEqual(data['tags'], [])
        self.assertEqual(data['axeStatus'], DesignSystemStory.AxeStatus.WARN)
