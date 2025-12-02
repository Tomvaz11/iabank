import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../shared/config/env', () => ({
  env: {
    API_BASE_URL: 'https://api.iabank.test',
    TENANT_DEFAULT: 'tenant-alfa',
    OTEL_EXPORTER_OTLP_ENDPOINT: 'http://localhost:4318',
    OTEL_SERVICE_NAME: 'frontend-foundation',
    OTEL_RESOURCE_ATTRIBUTES: {
      'service.namespace': 'iabank',
      'service.version': '0.1.0',
    },
    FOUNDATION_CSP_NONCE: 'nonce-dev',
    FOUNDATION_TRUSTED_TYPES_POLICY: 'foundation-ui',
    FOUNDATION_TRUSTED_TYPES_ROLLOUT_START: '2025-09-01T00:00:00.000Z',
    FOUNDATION_PGCRYPTO_KEY: 'dev-only',
  },
}));

describe('SecurityProvider', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllGlobals();
  });

  it('cria a Trusted Types policy quando suportada', async () => {
    const createPolicy = vi.fn().mockReturnValue({ name: 'foundation-ui' });
    const getPolicy = vi.fn().mockReturnValue(undefined);
    vi.stubGlobal('trustedTypes', {
      createPolicy,
      getPolicy,
    });

    const securityModule = await import('./security');

    render(
      <securityModule.SecurityProvider>
        <span>child</span>
      </securityModule.SecurityProvider>,
    );

    expect(screen.getByText('child')).toBeInTheDocument();
    expect(getPolicy).toHaveBeenCalledWith('foundation-ui');
    expect(createPolicy).toHaveBeenCalledWith(
      'foundation-ui',
      expect.objectContaining({
        createHTML: expect.any(Function),
        createScript: expect.any(Function),
        createScriptURL: expect.any(Function),
      }),
    );
  });

  it('reutiliza política existente quando já criada', async () => {
    const existingPolicy = { name: 'foundation-ui' };
    const createPolicy = vi.fn();
    const getPolicy = vi.fn().mockReturnValue(existingPolicy);
    vi.stubGlobal('trustedTypes', { createPolicy, getPolicy });

    const securityModule = await import('./security');

    render(
      <securityModule.SecurityProvider>
        <span>child</span>
      </securityModule.SecurityProvider>,
    );

    expect(createPolicy).not.toHaveBeenCalled();
  });

  it('não falha quando Trusted Types não está disponível', async () => {
    vi.stubGlobal('trustedTypes', undefined);
    const securityModule = await import('./security');

    expect(() =>
      render(
        <securityModule.SecurityProvider>
          <span>child</span>
        </securityModule.SecurityProvider>,
      ),
    ).not.toThrow();
  });

  it('permite reinicializar a policy após reset', async () => {
    const createPolicy = vi.fn().mockReturnValue({ name: 'foundation-ui' });
    const getPolicy = vi.fn().mockReturnValue(undefined);
    vi.stubGlobal('trustedTypes', { createPolicy, getPolicy });

    const securityModule = await import('./security');
    const first = securityModule.ensureTrustedTypesPolicy();
    expect(first?.name).toBe('foundation-ui');

    securityModule.resetTrustedTypesPolicy();
    const second = securityModule.ensureTrustedTypesPolicy();

    expect(createPolicy).toHaveBeenCalledTimes(2);
    expect(second?.name).toBe('foundation-ui');
  });

  it('retorna null quando API não suporta criação de policy', async () => {
    const getPolicy = vi.fn().mockReturnValue(null);
    vi.stubGlobal('trustedTypes', { getPolicy });

    const securityModule = await import('./security');
    expect(securityModule.ensureTrustedTypesPolicy()).toBeNull();
  });
});

describe('resolveTrustedTypesDisposition', () => {
  it('retorna report-only enquanto janela de rollout não expira', async () => {
    const securityModule = await import('./security');
    const resolve =
      securityModule.resolveTrustedTypesDisposition as (typeof import('./security'))['resolveTrustedTypesDisposition'];

    const result = resolve({
      startedAt: '2025-09-01T00:00:00Z',
      now: new Date('2025-09-10T00:00:00Z'),
    });

    expect(result.mode).toBe('report-only');
    expect(result.expiresAt.toISOString()).toBe('2025-10-01T00:00:00.000Z');
  });

  it('retorna enforce após expiração da janela', async () => {
    const securityModule = await import('./security');
    const resolve =
      securityModule.resolveTrustedTypesDisposition as (typeof import('./security'))['resolveTrustedTypesDisposition'];

    const result = resolve({
      startedAt: '2025-09-01T00:00:00Z',
      now: new Date('2025-11-15T00:00:00Z'),
    });

    expect(result.mode).toBe('enforce');
  });
});

describe('createSecurityViolationReporter', () => {
  it('encaminha violações trusted-types conforme o modo', async () => {
    const securityModule = await import('./security');
    const createReporter =
      securityModule.createSecurityViolationReporter as (typeof import('./security'))['createSecurityViolationReporter'];

    const reportOnlyViolations: SecurityPolicyViolationEvent[] = [];
    const enforcedViolations: SecurityPolicyViolationEvent[] = [];

    const reportOnlyHandler = createReporter({
      mode: 'report-only',
      reportOnlyThreshold: 2,
      onReportOnlyViolation: (violation) => reportOnlyViolations.push(violation),
      onEnforcedViolation: (violation) => enforcedViolations.push(violation),
    });

    const baseViolation = {
      violatedDirective: 'trusted-types foundation-ui',
      disposition: 'report',
    } as SecurityPolicyViolationEvent;

    reportOnlyHandler(baseViolation);
    expect(reportOnlyViolations).toHaveLength(1);
    expect(enforcedViolations).toHaveLength(0);

    reportOnlyHandler(baseViolation);
    expect(enforcedViolations).toHaveLength(1);

    const enforceHandler = createReporter({
      mode: 'enforce',
      reportOnlyThreshold: 1,
      onReportOnlyViolation: (violation) => reportOnlyViolations.push(violation),
      onEnforcedViolation: (violation) => enforcedViolations.push(violation),
    });

    enforceHandler({
      violatedDirective: 'trusted-types',
      disposition: 'enforce',
    } as SecurityPolicyViolationEvent);

    expect(enforcedViolations).toHaveLength(2);
  });

  it('ignora eventos que não são de trusted types', async () => {
    const securityModule = await import('./security');
    const createReporter =
      securityModule.createSecurityViolationReporter as (typeof import('./security'))['createSecurityViolationReporter'];

    const onReportOnlyViolation = vi.fn();
    const onEnforcedViolation = vi.fn();

    const reportOnlyHandler = createReporter({
      mode: 'report-only',
      reportOnlyThreshold: 1,
      onReportOnlyViolation,
      onEnforcedViolation,
    });

    reportOnlyHandler({
      violatedDirective: 'img-src',
      disposition: 'report',
    } as SecurityPolicyViolationEvent);

    expect(onReportOnlyViolation).not.toHaveBeenCalled();
    expect(onEnforcedViolation).not.toHaveBeenCalled();
  });
});
