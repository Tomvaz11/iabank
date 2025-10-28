import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/shared/config/env', () => ({
  env: {
    API_BASE_URL: 'https://api.iabank.test',
    TENANT_DEFAULT: 'tenant-alfa',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'https://otel.iabank.test/v1/traces',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    },
    CONFIGCAT_SDK_KEY: undefined,
    FOUNDATION_CSP_NONCE: 'nonce-dev',
    FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
    FOUNDATION_PGCRYPTO_KEY: 'pgcrypto-dev',
  },
}));

const createViolation = (
  overrides: Partial<SecurityPolicyViolationEvent>,
): SecurityPolicyViolationEvent =>
  ({
    blockedURI: overrides.blockedURI ?? 'inline',
    columnNumber: overrides.columnNumber ?? 0,
    documentURI: overrides.documentURI ?? 'https://app.iabank.test/dashboard',
    effectiveDirective: overrides.effectiveDirective ?? 'script-src',
    lineNumber: overrides.lineNumber ?? 0,
    originalPolicy: overrides.originalPolicy ?? '',
    referrer: overrides.referrer ?? '',
    sample: overrides.sample ?? '',
    sourceFile: overrides.sourceFile ?? '',
    statusCode: overrides.statusCode ?? 200,
    violatedDirective: overrides.violatedDirective ?? 'script-src',
    disposition: overrides.disposition ?? 'report',
  }) as SecurityPolicyViolationEvent;

describe('@SC-005 CSP e Trusted Types', () => {
  beforeEach(() => {
    vi.resetModules();
    delete (globalThis as unknown as { trustedTypes?: unknown }).trustedTypes;
  });

  it('calcula janela de rollout e cria policy Trusted Types foundation-ui', async () => {
    const createPolicy = vi.fn().mockReturnValue({
      createHTML: vi.fn((value: string) => value),
      createScript: vi.fn((value: string) => value),
      createScriptURL: vi.fn((value: string) => value),
    });

    (globalThis as unknown as { trustedTypes: unknown }).trustedTypes = {
      getPolicy: vi.fn().mockReturnValue(undefined),
      createPolicy,
    };

    const securityModule = (await import('../../src/app/providers/security')) as Record<
      string,
      unknown
    >;

    expect(typeof securityModule.resolveTrustedTypesDisposition).toBe('function');
    expect(typeof securityModule.createSecurityViolationReporter).toBe('function');

    const resolveDisposition = securityModule.resolveTrustedTypesDisposition as (input: {
      startedAt: string;
      now: Date;
    }) => { mode: 'report-only' | 'enforce'; expiresAt: Date };

    const beforeEnforce = resolveDisposition({
      startedAt: '2025-09-01T00:00:00Z',
      now: new Date('2025-09-15T00:00:00Z'),
    });
    expect(beforeEnforce.mode).toBe('report-only');
    expect(beforeEnforce.expiresAt.toISOString()).toBe('2025-10-01T00:00:00.000Z');

    const afterEnforce = resolveDisposition({
      startedAt: '2025-09-01T00:00:00Z',
      now: new Date('2025-11-05T12:00:00Z'),
    });
    expect(afterEnforce.mode).toBe('enforce');

    expect(createPolicy).toHaveBeenCalledWith(
      'foundation-ui',
      expect.objectContaining({
        createHTML: expect.any(Function),
        createScript: expect.any(Function),
        createScriptURL: expect.any(Function),
      }),
    );

    const createSecurityViolationReporter = securityModule.createSecurityViolationReporter as (input: {
      mode: 'report-only' | 'enforce';
      reportOnlyThreshold: number;
      onReportOnlyViolation: (violation: SecurityPolicyViolationEvent) => void;
      onEnforcedViolation: (violation: SecurityPolicyViolationEvent) => void;
    }) => (event: SecurityPolicyViolationEvent) => void;

    const reportOnlyWarnings: SecurityPolicyViolationEvent[] = [];
    const enforcedViolations: SecurityPolicyViolationEvent[] = [];

    const reportOnlyHandler = createSecurityViolationReporter({
      mode: 'report-only',
      reportOnlyThreshold: 3,
      onReportOnlyViolation: (violation) => {
        reportOnlyWarnings.push(violation);
      },
      onEnforcedViolation: (violation) => {
        enforcedViolations.push(violation);
      },
    });

    reportOnlyHandler(
      createViolation({
        disposition: 'report',
        violatedDirective: 'trusted-types',
        blockedURI: 'inline',
      }),
    );

    expect(reportOnlyWarnings).toHaveLength(1);
    expect(enforcedViolations).toHaveLength(0);

    const enforcedHandler = createSecurityViolationReporter({
      mode: 'enforce',
      reportOnlyThreshold: 1,
      onReportOnlyViolation: (violation) => {
        reportOnlyWarnings.push(violation);
      },
      onEnforcedViolation: (violation) => {
        enforcedViolations.push(violation);
      },
    });

    enforcedHandler(
      createViolation({
        disposition: 'enforce',
        violatedDirective: 'trusted-types',
        blockedURI: 'inline',
      }),
    );

    expect(enforcedViolations).toHaveLength(1);
    expect(enforcedViolations[0]?.violatedDirective).toBe('trusted-types');
  });
});
