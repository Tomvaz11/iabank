import { describe, expect, it } from 'vitest';

import {
  applyNonceToHtml,
  buildCspHeader,
  buildTrustedTypesReportHeader,
  createFoundationCspPlugin,
} from '../vite.csp.middleware';

describe('@SC-005 applyNonceToHtml', () => {
  it('injeta o atributo nonce nas tags de script sem duplicar', () => {
    const html = `<html><body><script type="module" src="/src/main.tsx"></script></body></html>`;
    const transformed = applyNonceToHtml(html, 'nonce-123');

    expect(transformed).toContain('<script nonce="nonce-123" type="module" src="/src/main.tsx"></script>');
  });

  it('mantém nonce existente se já estiver presente', () => {
    const html =
      `<html><body><script nonce="original" type="module" src="/src/main.tsx"></script></body></html>`;
    const transformed = applyNonceToHtml(html, 'nonce-123');

    expect(transformed).toContain('<script nonce="original" type="module" src="/src/main.tsx"></script>');
  });
});

describe('@SC-005 buildDevCspHeader', () => {
  it('produz diretivas esperadas com nonce e Trusted Types em modo enforce', () => {
    const header = buildCspHeader({
      nonce: 'nonce-123',
      trustedTypesPolicy: 'foundation-ui',
      reportUri: 'https://csp-report.iabank.test',
      connectSrc: ["'self'", 'https://api.iabank.test'],
      enforceTrustedTypes: true,
    });

    expect(header).toContain("script-src 'self' 'strict-dynamic' 'nonce-nonce-123'");
    expect(header).toContain("connect-src 'self' https://api.iabank.test");
    expect(header).toContain("require-trusted-types-for 'script'");
    expect(header).toContain('trusted-types foundation-ui');
    expect(header).toContain('report-uri https://csp-report.iabank.test');
  });

  it('gera header bloqueante sem require-trusted-types em report-only, mas ativa no report header', () => {
    const enforcement = buildCspHeader({
      nonce: 'nonce-abc',
      trustedTypesPolicy: 'foundation-ui',
      reportUri: null,
      enforceTrustedTypes: false,
    });

    const report = buildTrustedTypesReportHeader({
      nonce: 'nonce-abc',
      trustedTypesPolicy: 'foundation-ui',
      reportUri: null,
    });

    expect(enforcement).not.toContain("require-trusted-types-for 'script'");
    expect(report).toContain("require-trusted-types-for 'script'");
  });

  it('injeta script de runtime que promove Trusted Types após expiração do rollout', () => {
    const plugin = createFoundationCspPlugin({
      nonce: 'nonce-xyz',
      trustedTypesPolicy: 'foundation-ui',
      reportUri: 'https://csp-report.iabank.test',
      trustedTypesRolloutStart: '2025-09-01T00:00:00.000Z',
      now: () => new Date('2025-09-15T00:00:00.000Z'),
    }) as { transformIndexHtml?: (html: string) => string };

    const html =
      '<html><head></head><body><script type="module" src="/src/main.tsx"></script></body></html>';
    const transformed = plugin.transformIndexHtml ? plugin.transformIndexHtml(html) : html;

    expect(transformed).toContain('Content-Security-Policy');
    expect(transformed).toContain('Content-Security-Policy-Report-Only');
    expect(transformed).toContain('nonce="nonce-xyz"');
    expect(transformed).toContain('require-trusted-types-for \'script\'');
  });
});
