import path from 'node:path';

import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { expect, describe, it } from 'vitest';

import type { FeatureScaffoldRequest } from '../../../frontend/src/shared/api/generated/models/FeatureScaffoldRequest';
import { registerFeatureScaffold } from '../../../frontend/src/shared/api/client';
import { env } from '../../../frontend/src/shared/config/env';

const PACT_OUTPUT_DIR = path.resolve(__dirname, '..');
const TENANT_ID = 'a1b2c3d4-e5f6-7890-1234-567890abcdef';
const IDEMPOTENCY_KEY = '00000000-0000-4000-8000-000000000123';

const buildRequestPayload = (): FeatureScaffoldRequest => ({
  featureSlug: 'loan-tracking',
  initiatedBy: '0f7d5cf5-2367-4dbd-9d5d-1c2bde561111',
  slices: [
    {
      slice: 'features',
      files: [
        {
          path: 'src/features/loan-tracking/index.ts',
          checksum: '4a7d1ed414474e4033ac29ccb8653d9b00000000000000000000000000000000',
        },
      ],
    },
  ],
  lintCommitHash: '1234567890abcdef1234567890abcdef12345678',
  scReferences: ['@SC-001', '@SC-003'],
  durationMs: 2450,
  metadata: {
    cliVersion: '0.1.0',
  },
});

const overrideApiBaseUrl = (mockBaseUrl: string) => {
  env.API_BASE_URL = mockBaseUrl.replace(/\/+$/, '');
};

describe('Contrato consumer - registerFeatureScaffold', () => {
  const provider = new PactV3({
    consumer: 'FrontendFoundationScaffolding',
    provider: 'IABankFoundationAPI',
    dir: PACT_OUTPUT_DIR,
    spec: 3,
  });

  it('envia payload completo com headers obrigatórios e processa 201', async () => {
    const payload = buildRequestPayload();

    await provider
      .addInteraction({
        state: 'tenant possui capacidade de registrar scaffolding',
        uponReceiving: 'uma requisição para registrar scaffolding de feature',
        withRequest: {
          method: 'POST',
          path: `/api/v1/tenants/${TENANT_ID}/features/scaffold`,
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': IDEMPOTENCY_KEY,
            'X-Tenant-Id': TENANT_ID,
            traceparent: MatchersV3.like(
              '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00',
            ),
            tracestate: MatchersV3.like(`tenant-id=${TENANT_ID}`),
          },
          body: payload,
        },
        willRespondWith: {
          status: 201,
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            Location: MatchersV3.regex(
              /^\/api\/v1\/tenants\/[a-z0-9-]+\/features\/scaffold\/[a-z0-9-]+$/,
              `/api/v1/tenants/${TENANT_ID}/features/scaffold/${payload.featureSlug}`,
            ),
            'Idempotency-Key': MatchersV3.like(IDEMPOTENCY_KEY),
          },
          body: {
            scaffoldId: MatchersV3.uuid('20000000-0000-4000-8000-000000000000'),
            tenantId: TENANT_ID,
            status: 'initiated',
            recordedAt: MatchersV3.datetime('iso8601', '2025-01-01T12:00:00Z'),
            metrics: MatchersV3.eachLike({
              code: MatchersV3.regex(/^SC-00[1-5]$/, 'SC-001'),
              value: MatchersV3.like(275_000),
              collectedAt: MatchersV3.datetime('iso8601', '2025-01-01T12:00:00Z'),
              source: MatchersV3.regex(/^(ci|chromatic|lighthouse|manual)$/, 'ci'),
            }),
          },
        },
      })
      .executeTest(async (mockService) => {
        overrideApiBaseUrl(mockService.url);

        await expect(
          registerFeatureScaffold({
            tenantId: TENANT_ID,
            idempotencyKey: IDEMPOTENCY_KEY,
            payload,
            traceContext: {
              traceparent: '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00',
              tracestate: `tenant-id=${TENANT_ID}`,
            },
          }),
        ).resolves.toMatchObject({
          tenantId: TENANT_ID,
          status: 'initiated',
        });
      });
  });
});
