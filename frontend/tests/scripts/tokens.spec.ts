import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

import type { TenantThemeResponse } from '../../scripts/tokens/index';
import { buildTenantArtifacts, pullTenantTokens } from '../../scripts/tokens/index';

const SAMPLE_RESPONSE: TenantThemeResponse = {
  tenantId: '00000000-0000-0000-0000-000000000001',
  version: '1.0.0',
  generatedAt: '2025-10-20T12:00:00Z',
  categories: {
    foundation: {
      'color.brand.primary': '#1E3A8A',
    },
    semantic: {
      'surface.background': '#ffffff',
    },
    component: {
      'button.primary.bg': '#1E3A8A',
    },
  },
  wcagReport: {
    semantic: {
      contrast: 'AA',
    },
  },
};

describe('foundation:tokens script', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = mkdtempSync(path.join(tmpdir(), 'tokens-script-'));
  });

  afterEach(() => {
    rmSync(tempDir, { recursive: true, force: true });
  });

  it('pullTenantTokens salva resposta no cache com alias', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(SAMPLE_RESPONSE), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ETag: '"abc123"' },
      }),
    );

    const result = await pullTenantTokens({
      tenantId: SAMPLE_RESPONSE.tenantId,
      tenantAlias: 'tenant-alfa',
      endpoint: 'https://api.iabank.test',
      cacheDir: tempDir,
      fetchImpl: fetchMock,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      'https://api.iabank.test/api/v1/tenants/00000000-0000-0000-0000-000000000001/themes/current',
      {
        headers: {
          'Accept': 'application/json',
          'X-Tenant-Id': SAMPLE_RESPONSE.tenantId,
        },
      },
    );

    const cacheFile = path.join(tempDir, `${SAMPLE_RESPONSE.tenantId}.json`);
    const stored = JSON.parse(readFileSync(cacheFile, 'utf-8')) as Awaited<
      ReturnType<typeof pullTenantTokens>
    >;

    expect(stored.alias).toBe('tenant-alfa');
    expect(stored.tenantId).toBe(SAMPLE_RESPONSE.tenantId);
    expect(stored.etag).toBe('"abc123"');
    expect(stored.payload.version).toBe('1.0.0');
  });

  it('buildTenantArtifacts gera arquivos TypeScript e CSS', async () => {
    const cacheFile = path.join(tempDir, `${SAMPLE_RESPONSE.tenantId}.json`);
    writeFileSync(
      cacheFile,
      JSON.stringify(
        {
          alias: 'tenant-alfa',
          tenantId: SAMPLE_RESPONSE.tenantId,
          etag: '"abc123"',
          payload: SAMPLE_RESPONSE,
        },
        null,
        2,
      ),
      'utf-8',
    );

    const configPath = path.join(tempDir, 'tenants.ts');
    const cssPath = path.join(tempDir, 'tokens.css');

    await buildTenantArtifacts({
      cacheDir: tempDir,
      tenantsConfigPath: configPath,
      tokensCssPath: cssPath,
    });

    const tsContent = readFileSync(configPath, 'utf-8');
    expect(tsContent).toContain("export const tenantTokens: Record<string, TenantTokenCategories> = {\n  'tenant-alfa': {");
    expect(tsContent).toContain("'color.brand.primary': '#1E3A8A'");
    expect(tsContent).toContain("'button.primary.bg': '#1E3A8A'");

    const cssContent = readFileSync(cssPath, 'utf-8');
    expect(cssContent).toContain('html[data-tenant=\"tenant-alfa\"]');
    expect(cssContent).toContain('--color-brand-primary: #1E3A8A;');
    expect(cssContent).toContain('--button-primary-bg: #1E3A8A;');
  });

  it('rejeita payload sem categorias válidas', async () => {
    const invalidResponse = {
      ...SAMPLE_RESPONSE,
      categories: {
        foundation: {
          'color.brand.primary': 123,
        },
      },
    } satisfies Partial<TenantThemeResponse> as TenantThemeResponse;

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(invalidResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      pullTenantTokens({
        tenantId: SAMPLE_RESPONSE.tenantId,
        fetchImpl: fetchMock,
        tenantAlias: 'tenant-alfa',
        endpoint: 'https://api.iabank.test',
      }),
    ).rejects.toThrow(/TokenSchema/);
  });
});
