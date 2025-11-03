import { describe, expect, it } from 'vitest';

describe('@SC-005 sanitizeTelemetryAttributes', () => {
  it('mascara PII mantendo atributos em allowlist', async () => {
    const module = (await import('../../src/shared/lib/telemetry/masking')) as Record<
      string,
      unknown
    >;

    expect(typeof module.sanitizeTelemetryAttributes).toBe('function');

    const sanitize = module.sanitizeTelemetryAttributes as (
      attributes: Record<string, unknown>,
    ) => Record<string, unknown>;

    const sanitized = sanitize({
      tenant_id: 'tenant-alfa',
      feature_slug: 'loan-tracking',
      customerCpf: '123.456.789-09',
      customerEmail: 'user@example.com',
      contactPhone: '+55 11 91234-5678',
      freeText: 'CPF: 123.456.789-09 e email user@example.com',
      amount: 1234,
    });

    expect(sanitized.tenant_id).toBe('tenant-alfa');
    expect(sanitized.feature_slug).toBe('loan-tracking');
    expect(sanitized.amount).toBe(1234);
    expect(sanitized.customerCpf).toBe('[PII]');
    expect(sanitized.customerEmail).toBe('[PII]');
    expect(sanitized.contactPhone).toBe('[PII]');
    expect(sanitized.freeText).toBe('[PII]');
  });

  it('não duplica mascaramento já aplicado', async () => {
    const module = (await import('../../src/shared/lib/telemetry/masking')) as Record<
      string,
      unknown
    >;

    expect(typeof module.sanitizeTelemetryAttributes).toBe('function');

    const sanitize = module.sanitizeTelemetryAttributes as (
      attributes: Record<string, unknown>,
    ) => Record<string, unknown>;

    const sanitized = sanitize({
      tenant_id: 'tenant-beta',
      status: 'ok',
      alreadyRedacted: '[PII]',
      customFlag: 'SAFE',
      suspicious: 'email: mask@iabank.com',
    });

    expect(sanitized.status).toBe('ok');
    expect(sanitized.alreadyRedacted).toBe('[PII]');
    expect(sanitized.customFlag).toBe('SAFE');
    expect(sanitized.suspicious).toBe('[PII]');
  });
});
