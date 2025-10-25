import path from 'node:path';

import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { describe, expect, it } from 'vitest';

import { getTenantTheme } from '../../../frontend/src/shared/api/client';
import { env } from '../../../frontend/src/shared/config/env';

const PACT_OUTPUT_DIR = path.resolve(__dirname, '..');
const TENANT_ID = 'a1b2c3d4-e5f6-7890-1234-567890abcdef';

const overrideApiBaseUrl = (mockBaseUrl: string) => {
  env.API_BASE_URL = mockBaseUrl.replace(/\/+$/, '');
};

describe('Contrato consumer - getTenantTheme', () => {
  const provider = new PactV3({
    consumer: 'FrontendFoundationTheme',
    provider: 'IABankFoundationAPI',
    dir: PACT_OUTPUT_DIR,
    spec: 3,
  });

  it('busca tokens vigentes do tenant com rastreabilidade e caching controlado', async () => {
    const traceparent = '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01';
    const tracestate = `tenant-id=${TENANT_ID}`;

    await provider
      .addInteraction({
        state: 'tenant possui tokens fundacionais ativos',
        uponReceiving: 'uma requisição para recuperar o tema corrente do tenant',
        withRequest: {
          method: 'GET',
          path: `/api/v1/tenants/${TENANT_ID}/themes/current`,
          headers: {
            'X-Tenant-Id': TENANT_ID,
            traceparent: MatchersV3.like(traceparent),
            tracestate: MatchersV3.like(tracestate),
          },
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            ETag: MatchersV3.regex(/^W\/\"[a-f0-9]{32}\"$/, 'W/"0123456789abcdef0123456789abcdef"'),
            'RateLimit-Limit': MatchersV3.integer(300),
            'RateLimit-Remaining': MatchersV3.integer(299),
            'RateLimit-Reset': MatchersV3.like('2025-01-01T12:00:00Z'),
          },
          body: {
            tenantId: TENANT_ID,
            version: MatchersV3.regex(/^\d+\.\d+\.\d+$/, '1.2.3'),
            generatedAt: MatchersV3.datetime('iso8601', '2025-01-01T12:00:00Z'),
            categories: MatchersV3.like({
              foundation: {
                colorPrimary: '#0A66C2',
                colorOnPrimary: '#FFFFFF',
              },
              semantic: {
                infoDefault: '#2563EB',
              },
            }),
            wcagReport: MatchersV3.like({
              contrastRatio: 4.5,
              status: 'pass',
            }),
          },
        },
      })
      .executeTest(async (mockService) => {
        overrideApiBaseUrl(mockService.url);

        const response = await getTenantTheme({
          tenantId: TENANT_ID,
          traceContext: {
            traceparent,
            tracestate,
          },
        });

        expect(response).toMatchObject({
          tenantId: TENANT_ID,
          version: '1.2.3',
          categories: expect.objectContaining({
            foundation: expect.any(Object),
          }),
        });
      });
  });
});
