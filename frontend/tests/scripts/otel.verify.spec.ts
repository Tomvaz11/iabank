import { describe, expect, it } from 'vitest';

import { verifyTelemetry } from '../../scripts/otel/verify';

describe('foundation:otel verify CLI', () => {
  it('gera trace com baggage e aplica mascaramento de PII', async () => {
    const report = await verifyTelemetry({
      tenantId: 'tenant-alfa',
      featureSlug: 'loan-tracking',
      endpoint: 'http://localhost:4318/v1/traces',
      serviceName: 'frontend-foundation',
      resourceAttributes: {
        'service.namespace': 'iabank',
        'service.version': '0.1.0',
      },
      additionalAttributes: {
        customerEmail: 'user@example.com',
        contactPhone: '+55 11 91234-5678',
      },
      dryRun: true,
    });

    expect(report.spanName).toBe('FOUNDATION-TENANT-BOOTSTRAP');
    expect(report.attributes['app.tenant_id']).toBe('tenant-alfa');
    expect(report.attributes['app.feature_slug']).toBe('loan-tracking');
    expect(report.attributes.customerEmail).toBe('[PII]');
    expect(report.attributes.contactPhone).toBe('[PII]');
    expect(report.maskedKeys).toEqual(expect.arrayContaining(['customerEmail', 'contactPhone']));
    expect(report.baggage['tenant.id']).toBe('tenant-alfa');
    expect(report.baggage['feature.slug']).toBe('loan-tracking');
    expect(report.exportedSpans).toBe(1);
    expect(report.errors).toHaveLength(0);
  });

  it('falha quando tenantId não é informado', async () => {
    await expect(
      verifyTelemetry({
        tenantId: '',
        featureSlug: 'loan-tracking',
        endpoint: 'http://localhost:4318/v1/traces',
        serviceName: 'frontend-foundation',
        resourceAttributes: {
          'service.namespace': 'iabank',
        },
        dryRun: true,
      }),
    ).rejects.toThrow(/tenant/i);
  });
});
