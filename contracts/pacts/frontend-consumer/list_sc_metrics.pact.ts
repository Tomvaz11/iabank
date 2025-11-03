import path from 'node:path';

import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { describe, expect, it } from 'vitest';

import { listTenantSuccessMetrics } from '../../../frontend/src/shared/api/client';
import { env } from '../../../frontend/src/shared/config/env';

const PACT_OUTPUT_DIR = path.resolve(__dirname, '..');
const TENANT_ID = 'tenant-alfa';

const overrideApiBaseUrl = (mockBaseUrl: string) => {
  env.API_BASE_URL = mockBaseUrl.replace(/\/+$/, '');
};

describe('Contrato consumer - listTenantSuccessMetrics', () => {
  const provider = new PactV3({
    consumer: 'FrontendFoundationMetrics',
    provider: 'IABankFoundationAPI',
    dir: PACT_OUTPUT_DIR,
    spec: 3,
  });

  it('lista métricas SC com cabeçalhos de rate limit e paginação', async () => {
    const traceparent = '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01';
    const tracestate = `tenant-id=${TENANT_ID}`;

    await provider
      .given('tenant possui métricas SC agregadas para dashboards')
      .uponReceiving('uma requisição para listar métricas SC do tenant')
      .withRequest({
        method: 'GET',
        path: `/api/v1/tenant-metrics/${TENANT_ID}/sc`,
        headers: {
          'X-Tenant-Id': TENANT_ID,
          traceparent: MatchersV3.like(traceparent),
          tracestate: MatchersV3.like(tracestate),
        },
        query: {
          page: '1',
          page_size: '25',
        },
      })
      .willRespondWith({
        status: 200,
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'RateLimit-Limit': MatchersV3.like('60'),
          'RateLimit-Remaining': MatchersV3.like('59'),
          'RateLimit-Reset': MatchersV3.like('30'),
        },
        body: {
          data: MatchersV3.eachLike({
            code: MatchersV3.regex(/^SC-00[1-5]$/, 'SC-001'),
            value: MatchersV3.like(0.92),
            collectedAt: MatchersV3.datetime('iso8601', '2025-01-10T12:00:00Z'),
            source: MatchersV3.regex(/^(ci|chromatic|lighthouse|manual)$/, 'ci'),
          }),
          pagination: {
            page: MatchersV3.like(1),
            perPage: MatchersV3.like(25),
            totalItems: MatchersV3.like(1),
            totalPages: MatchersV3.like(1),
          },
        },
      })
      .executeTest(async (mockService) => {
        overrideApiBaseUrl(mockService.url);

        const response = await listTenantSuccessMetrics({
          tenantId: TENANT_ID,
          page: 1,
          pageSize: 25,
          traceContext: {
            traceparent,
            tracestate,
          },
        });

        expect(response.data).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              code: 'SC-001',
              value: expect.any(Number),
            }),
          ]),
        );
        expect(response.pagination.totalItems).toBeGreaterThanOrEqual(1);
      });
  });
});
