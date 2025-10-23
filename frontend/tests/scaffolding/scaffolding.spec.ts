import { randomUUID } from 'node:crypto';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const TENANT_ID = 'tenant-alfa';
const FEATURE_SLUG = 'loan-tracking';
const IDEMPOTENCY_KEY = '00000000-0000-4000-8000-000000000123';
const TAGS = ['@SC-001', '@SC-003'];
const AUTHOR_ID = '11111111-2222-4333-8444-555555555555';

const registerFeatureScaffoldMock = vi.fn().mockResolvedValue({
  data: {
    scaffoldId: randomUUID(),
    tenantId: TENANT_ID,
    status: 'initiated',
    recordedAt: new Date().toISOString(),
  },
});

vi.mock('../../src/shared/api/client', async () => {
  const actual = await vi.importActual<typeof import('../../src/shared/api/client')>(
    '../../src/shared/api/client',
  );
  return {
    ...actual,
    registerFeatureScaffold: registerFeatureScaffoldMock,
  };
});

const createTempWorkspace = async () => {
  const tempDir = await mkdtemp(path.join(os.tmpdir(), 'foundation-scaffold-'));
  return tempDir;
};

describe('CLI foundation:scaffold', () => {
  let workspaceRoot: string;

  beforeEach(async () => {
    workspaceRoot = await createTempWorkspace();
    registerFeatureScaffoldMock.mockClear();
  });

  afterEach(async () => {
    if (workspaceRoot) {
      await rm(workspaceRoot, { recursive: true, force: true });
    }
  });

  it('gera estrutura FSD, calcula manifest e registra scaffolding no backend', async () => {
    const mod = await import('../../scripts/scaffolding/index');
    const runScaffoldingCommand = mod.runScaffoldingCommand;

    if (typeof runScaffoldingCommand !== 'function') {
      throw new Error('runScaffoldingCommand deve ser exportada por frontend/scripts/scaffolding/index.ts');
    }

    const result = await runScaffoldingCommand({
      featureSlug: FEATURE_SLUG,
      tenantId: TENANT_ID,
      tags: TAGS,
      idempotencyKey: IDEMPOTENCY_KEY,
      initiatedBy: AUTHOR_ID,
      projectRoot: workspaceRoot,
    });

    expect(result).toMatchObject({
      featureSlug: FEATURE_SLUG,
      durationMs: expect.any(Number),
      manifestPath: expect.stringContaining('scaffold-manifest.json'),
    });

    expect(registerFeatureScaffoldMock).toHaveBeenCalledTimes(1);

    const [call] = registerFeatureScaffoldMock.mock.calls;
    const { tenantId, idempotencyKey, payload, traceContext } = call;

    expect({ tenantId, idempotencyKey }).toEqual({
      tenantId: TENANT_ID,
      idempotencyKey: IDEMPOTENCY_KEY,
    });

    expect(traceContext).toMatchObject({
      traceparent: expect.stringMatching(/^00-[0-9a-f]{32}-[0-9a-f]{16}-0[0-3]$/),
      tracestate: `tenant-id=${TENANT_ID}`,
    });

    expect(payload).toMatchObject({
      featureSlug: FEATURE_SLUG,
      initiatedBy: AUTHOR_ID,
      scReferences: TAGS,
      durationMs: expect.any(Number),
    });

    expect(payload.lintCommitHash).toMatch(/^[0-9a-f]{40}$/);
    expect(payload.metadata?.cliVersion).toBeDefined();

    const sliceNames = payload.slices.map((slice) => slice.slice);
    expect(sliceNames).toEqual(
      expect.arrayContaining(['app', 'pages', 'features', 'entities', 'shared']),
    );

    payload.slices.forEach((slice) => {
      expect(slice.files.length).toBeGreaterThan(0);
      slice.files.forEach((file) => {
        expect(file.path).toMatch(/\.(ts|tsx|css)$/);
        expect(file.checksum).toMatch(/^[0-9a-f]{64}$/);
      });
    });

    const fsdLayers = await readdir(workspaceRoot);
    expect(fsdLayers).toEqual(
      expect.arrayContaining(['app', 'pages', 'features', 'entities', 'shared']),
    );

    const manifestContents = await readFile(result.manifestPath, 'utf-8');
    expect(JSON.parse(manifestContents)).toMatchObject({
      feature: FEATURE_SLUG,
      files: expect.any(Array),
    });
  });
});
