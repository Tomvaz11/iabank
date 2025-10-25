from __future__ import annotations

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.foundation.models import DesignSystemStory
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class ListDesignSystemStoriesApiTest(APITestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant_alfa = Tenant.objects.create(
            slug='tenant-alfa',
            display_name='Tenant Alfa',
            primary_domain='tenant-alfa.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )
        self.tenant_beta = Tenant.objects.create(
            slug='tenant-beta',
            display_name='Tenant Beta',
            primary_domain='tenant-beta.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )

        with use_tenant(self.tenant_alfa.id):
            self.theme_alfa = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary': '#1E3A8A'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

        with use_tenant(self.tenant_beta.id):
            self.theme_beta = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary': '#6B7280'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

        self.story_button = DesignSystemStory.objects.create(
            tenant=self.tenant_alfa,
            theme_token=self.theme_alfa,
            component_id='shared/ui/button',
            story_id='Primary',
            tags=['critical', 'button'],
            coverage_percent=Decimal('98.5'),
            axe_status=DesignSystemStory.AxeStatus.PASS,
            axe_results={'violations': []},
            chromatic_build='build-001',
            storybook_url='https://chromatic.example.com/story/button-primary',
        )

        self.story_card = DesignSystemStory.objects.create(
            tenant=self.tenant_beta,
            theme_token=self.theme_beta,
            component_id='shared/ui/card',
            story_id='Overview',
            tags=['card', 'secondary'],
            coverage_percent=Decimal('96.0'),
            axe_status=DesignSystemStory.AxeStatus.WARN,
            axe_results={'violations': [{'id': 'color-contrast'}]},
            chromatic_build='build-002',
            storybook_url='https://chromatic.example.com/story/card-overview',
        )

    def _url(self) -> str:
        return reverse('foundation:list-design-system-stories')

    def test_lists_stories_with_pagination_details(self) -> None:
        response = self.client.get(
            self._url(),
            data={'page': 1, 'page_size': 1},
            HTTP_TRACEPARENT='00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('ETag', response)

        payload = response.json()
        self.assertIn('data', payload)
        self.assertIn('pagination', payload)
        self.assertEqual(payload['pagination']['page'], 1)
        self.assertEqual(payload['pagination']['perPage'], 1)
        self.assertEqual(payload['pagination']['totalItems'], 2)
        self.assertEqual(payload['pagination']['totalPages'], 2)

        first_story = payload['data'][0]
        self.assertIn('componentId', first_story)
        self.assertIn('axeStatus', first_story)
        self.assertIn('coveragePercent', first_story)

    def test_filters_by_component_id_and_tag(self) -> None:
        response = self.client.get(
            self._url(),
            data={'componentId': 'shared/ui/button', 'tag': 'critical'},
            HTTP_TRACEPARENT='00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-02',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)
        story = payload['data'][0]
        self.assertEqual(story['componentId'], 'shared/ui/button')
        self.assertIn('critical', story['tags'])

    def test_filters_by_tenant_header(self) -> None:
        response = self.client.get(
            self._url(),
            HTTP_X_TENANT_ID=str(self.tenant_beta.id),
            HTTP_TRACEPARENT='00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-03',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(len(payload['data']), 1)
        self.assertEqual(payload['data'][0]['tenantId'], str(self.tenant_beta.id))
