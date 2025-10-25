import path from 'node:path';

import { PactV3 } from '@pact-foundation/pact';

import { listDesignSystemStories } from '../../src/shared/api/client';
import { env } from '../../src/shared/config/env';

const TENANT_ID = 'tenant-alfa';
const PACT_DIR = path.resolve(__dirname, '../../pacts');

describe('Design system stories API contract', () => {
  const provider = new PactV3({
    consumer: 'FrontendFoundationDesignSystem',
    provider: 'IABankFoundationAPI',
    dir: PACT_DIR,
    spec: 3,
  });

  const overrideApiBaseUrl = (mockBaseUrl: string) => {
    env.API_BASE_URL = mockBaseUrl.replace(/\/+$/, '');
  };

  it('lista stories com filtros opcionais aplicados', async () => {
    await provider
      .addInteraction({
        state: 'existem stories publicados para tenant-alfa',
        uponReceiving: 'uma requisição para listar stories filtradas',
        withRequest: {
          method: 'GET',
          path: '/api/v1/design-system/stories',
          query: {
            page: '1',
            page_size: '10',
            componentId: 'shared/ui/button',
            tag: 'critical',
          },
          headers: {
            'X-Tenant-Id': TENANT_ID,
            traceparent: '00-ffffffffffffffffffffffffffffffff-eeeeeeeeeeeeeeee-01',
            tracestate: 'tenant-id=tenant-alfa',
          },
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            ETag: '"stories-tenant-alfa-v1"',
          },
          body: {
            data: [
              {
                id: 'f3a1b2c3-d4e5-6789-8abc-def012345678',
                tenantId: TENANT_ID,
                componentId: 'shared/ui/button',
                storyId: 'Primary',
                tags: ['critical', 'button'],
                coveragePercent: 98.5,
                axeStatus: 'pass',
                chromaticBuild: 'build-001',
                storybookUrl: 'https://chromatic.example.com/story/button-primary',
                updatedAt: '2025-01-01T12:00:00Z',
              },
            ],
            pagination: {
              page: 1,
              perPage: 10,
              totalItems: 1,
              totalPages: 1,
            },
          },
        },
      })
      .executeTest(async (mockService) => {
        overrideApiBaseUrl(mockService.url);

        const response = await listDesignSystemStories({
          tenantId: TENANT_ID,
          page: 1,
          pageSize: 10,
          traceContext: {
            traceparent: '00-ffffffffffffffffffffffffffffffff-eeeeeeeeeeeeeeee-01',
            tracestate: 'tenant-id=tenant-alfa',
          },
          filters: {
            componentId: 'shared/ui/button',
            tag: 'critical',
          },
        });

        expect(response.data).toHaveLength(1);
        expect(response.data[0].componentId).toBe('shared/ui/button');
        expect(response.pagination.totalItems).toBe(1);
      });
  });
});
