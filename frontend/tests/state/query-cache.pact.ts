import { pactWith } from '@pact-foundation/pact';

import {
  getTenantTheme,
  registerFeatureScaffold,
  listTenantSuccessMetrics,
} from '../../src/shared/api/client';

const TENANT_ID = 'tenant-alfa';

pactWith(
  {
    consumer: 'FrontendFoundationQueryCache',
    provider: 'IABankFoundationAPI',
    dir: 'pacts',
    spec: 3,
  },
  (interaction) => {
    describe('TanStack Query cache governance', () => {
      interaction('GET /api/v1/tenants/{tenantId}/themes/current', ({ provider }) => {
        it('propaga headers de tenant e trace context', async () => {
          await provider
            .given('tenant-alfa possui tema foundation v1.0.0')
            .uponReceiving('uma requisição para carregar o tema atual do tenant')
            .withRequest({
              method: 'GET',
              path: `/api/v1/tenants/${TENANT_ID}/themes/current`,
              headers: {
                'X-Tenant-Id': TENANT_ID,
                traceparent: '00-1234567890abcdef1234567890abcdef-1234567890abcdef-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
            })
            .willRespondWith({
              status: 200,
              headers: {
                'Content-Type': 'application/json; charset=utf-8',
                ETag: 'W/"tenant-alfa-theme-v1.0.0"',
              },
              body: {
                data: {
                  id: 'tenant-alfa-theme',
                  version: '1.0.0',
                  tokens: [],
                },
              },
            });

          await expect(
            getTenantTheme({
              tenantId: TENANT_ID,
              traceContext: {
                traceparent: '00-1234567890abcdef1234567890abcdef-1234567890abcdef-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
            }),
          ).resolves.toMatchObject({
            data: {
              id: 'tenant-alfa-theme',
            },
          });
        });
      });

      interaction('POST /api/v1/tenants/{tenantId}/features/scaffold', ({ provider }) => {
        it('registra scaffolding com idempotency key', async () => {
          await provider
            .given('tenant-alfa possui scaffolding pendente para loan-tracking')
            .uponReceiving('uma requisição para registrar scaffolding de feature')
            .withRequest({
              method: 'POST',
              path: `/api/v1/tenants/${TENANT_ID}/features/scaffold`,
              headers: {
                'X-Tenant-Id': TENANT_ID,
                'Idempotency-Key': '00000000-0000-0000-0000-000000000001',
                'Content-Type': 'application/json',
                traceparent: '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
              body: {
                featureSlug: 'loan-tracking',
                slice: 'features',
                scaffoldManifest: {},
                tags: ['@SC-001', '@SC-003'],
              },
            })
            .willRespondWith({
              status: 201,
              headers: {
                Location: '/features/scaffold/loan-tracking',
                'Idempotency-Key': '00000000-0000-0000-0000-000000000001',
              },
              body: {
                data: {
                  featureSlug: 'loan-tracking',
                  tenantId: TENANT_ID,
                  status: 'initiated',
                },
              },
            });

          await expect(
            registerFeatureScaffold({
              tenantId: TENANT_ID,
              idempotencyKey: '00000000-0000-0000-0000-000000000001',
              payload: {
                featureSlug: 'loan-tracking',
                slice: 'features',
                scaffoldManifest: {},
                tags: ['@SC-001', '@SC-003'],
              },
              traceContext: {
                traceparent: '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
            }),
          ).resolves.toMatchObject({
            data: {
              status: 'initiated',
            },
          });
        });
      });

      interaction('GET /tenant-metrics', ({ provider }) => {
        it('consulta métricas SC com paginação', async () => {
          await provider
            .given('tenant-alfa possui métricas SC registradas')
            .uponReceiving('uma requisição para listar métricas SC por tenant')
            .withRequest({
              method: 'GET',
              path: `/api/v1/tenant-metrics/${TENANT_ID}/sc`,
              query: 'page=1&pageSize=25',
              headers: {
                'X-Tenant-Id': TENANT_ID,
                traceparent: '00-cccccccccccccccccccccccccccccccc-dddddddddddddddd-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
            })
            .willRespondWith({
              status: 200,
              headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'RateLimit-Limit': '60',
                'RateLimit-Remaining': '59',
                'RateLimit-Reset': '30',
              },
              body: {
                data: [
                  {
                    metricId: 'SC-001',
                    tenantId: TENANT_ID,
                    value: 0.92,
                  },
                ],
                meta: {
                  page: 1,
                  pageSize: 25,
                  total: 1,
                },
              },
            });

          await expect(
            listTenantSuccessMetrics({
              tenantId: TENANT_ID,
              page: 1,
              pageSize: 25,
              traceContext: {
                traceparent: '00-cccccccccccccccccccccccccccccccc-dddddddddddddddd-00',
                tracestate: 'tenant-id=tenant-alfa',
              },
            }),
          ).resolves.toMatchObject({
            data: expect.arrayContaining([
              expect.objectContaining({
                metricId: 'SC-001',
              }),
            ]),
          });
        });
      });
    });
  },
);
