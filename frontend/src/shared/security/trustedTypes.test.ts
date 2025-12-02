import { describe, expect, it } from 'vitest';

import { resolveTrustedTypesDisposition } from './trustedTypes';

describe('shared/security/trustedTypes', () => {
  it('usa modo report-only quando start inválido e janela não expirou', () => {
    const { mode } = resolveTrustedTypesDisposition({
      startedAt: 'invalid-date',
      now: new Date(Date.now()),
    });

    expect(mode).toBe('report-only');
  });

  it('usa modo enforce após expiração da janela', () => {
    const start = '2025-09-01T00:00:00Z';
    const { mode } = resolveTrustedTypesDisposition({
      startedAt: start,
      now: new Date('2025-11-15T00:00:00Z'),
    });

    expect(mode).toBe('enforce');
  });
});
