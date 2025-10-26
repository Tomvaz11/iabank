import { describe, expect, it } from 'vitest';

import { applyNonceToHtml, buildDevCspHeader } from '../vite.csp.middleware';

describe('applyNonceToHtml', () => {
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

describe('buildDevCspHeader', () => {
  it('produz diretivas esperadas com nonce e Trusted Types', () => {
    const header = buildDevCspHeader({
      nonce: 'nonce-123',
      trustedTypesPolicy: 'foundation-ui',
      reportUri: 'https://csp-report.iabank.test',
      connectSrc: ["'self'", 'https://api.iabank.test'],
    });

    expect(header).toContain("script-src 'self' 'strict-dynamic' 'nonce-nonce-123'");
    expect(header).toContain("connect-src 'self' https://api.iabank.test");
    expect(header).toContain("require-trusted-types-for 'script'");
    expect(header).toContain('trusted-types foundation-ui');
    expect(header).toContain('report-uri https://csp-report.iabank.test');
  });
});
