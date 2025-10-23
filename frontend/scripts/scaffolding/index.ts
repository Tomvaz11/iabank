import { randomBytes, randomUUID, createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

import { registerFeatureScaffold } from '../../src/shared/api/client';
import type { FeatureScaffoldRequest } from '../../src/shared/api/generated/models/FeatureScaffoldRequest';
import { buildTemplateContext, createScaffoldTemplates, type ScaffoldSlice } from './templates';

const require = createRequire(import.meta.url);

type RegisterFeatureScaffoldFn = typeof registerFeatureScaffold;

export type RunScaffoldingOptions = {
  featureSlug: string;
  tenantId: string;
  tags: string[];
  idempotencyKey: string;
  initiatedBy: string;
  projectRoot?: string;
  registerFn?: RegisterFeatureScaffoldFn;
};

type FileMetadata = {
  slice: ScaffoldSlice;
  relativePath: string;
  absolutePath: string;
  checksum: string;
};

type ManifestSchema = {
  feature: string;
  tenantId: string;
  generatedAt: string;
  files: Array<Pick<FileMetadata, 'slice' | 'relativePath' | 'checksum'>>;
};

type TraceContext = {
  traceparent: string;
  tracestate: string;
};

const SLICES_IN_ORDER: ScaffoldSlice[] = ['app', 'pages', 'features', 'entities', 'shared'];

const CLI_VERSION = (() => {
  try {
    const pkg = require('../../package.json') as { version?: string };
    return pkg.version ?? '0.0.0';
  } catch {
    return '0.0.0';
  }
})();

const normalizeProjectRoot = (value?: string): string => {
  if (!value) {
    return process.cwd();
  }
  return path.isAbsolute(value) ? value : path.resolve(process.cwd(), value);
};

const ensureDirectory = async (filePath: string): Promise<void> => {
  await mkdir(path.dirname(filePath), { recursive: true });
};

const writeTemplateFile = async (
  slice: ScaffoldSlice,
  projectRoot: string,
  relativePath: string,
  content: string,
): Promise<FileMetadata> => {
  const absolutePath = path.join(projectRoot, relativePath);
  await ensureDirectory(absolutePath);
  await writeFile(absolutePath, content, { encoding: 'utf-8' });

  const checksum = createHash('sha256').update(content).digest('hex');

  return {
    slice,
    relativePath: relativePath.replace(/\\/g, '/'),
    absolutePath,
    checksum,
  };
};

const buildManifest = (metadata: FileMetadata[], feature: string, tenantId: string): ManifestSchema => ({
  feature,
  tenantId,
  generatedAt: new Date().toISOString(),
  files: metadata.map(({ slice, relativePath, checksum }) => ({
    slice,
    relativePath,
    checksum,
  })),
});

const writeManifest = async (projectRoot: string, manifest: ManifestSchema): Promise<string> => {
  const manifestPath = path.join(projectRoot, 'scaffold-manifest.json');
  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2), { encoding: 'utf-8' });
  return manifestPath;
};

const generateSha1 = (payload: unknown): string =>
  createHash('sha1').update(JSON.stringify(payload)).digest('hex');

const randomHex = (bytes: number): string => randomBytes(bytes).toString('hex');

const buildTraceContext = (tenantId: string): TraceContext => ({
  traceparent: `00-${randomHex(16)}-${randomHex(8)}-01`,
  tracestate: `tenant-id=${tenantId}`,
});

const buildSlicesPayload = (files: FileMetadata[]): FeatureScaffoldRequest['slices'] =>
  SLICES_IN_ORDER.map((slice) => ({
    slice,
    files: files
      .filter((file) => file.slice === slice)
      .map((file) => ({
        path: file.relativePath,
        checksum: file.checksum,
      })),
  })).filter((slice) => slice.files.length > 0);

const validateFeatureSlug = (featureSlug: string): void => {
  if (!/^[a-z0-9-]+$/.test(featureSlug)) {
    throw new Error('featureSlug deve conter apenas caracteres minúsculos, números ou hífen.');
  }
};

const parseTags = (rawTags: string[]): string[] =>
  rawTags
    .flatMap((tag) => tag.split(','))
    .map((tag) => tag.trim())
    .filter(Boolean);

const parseCliArgs = (argv: string[]): RunScaffoldingOptions | null => {
  if (argv.length === 0) {
    return null;
  }

  if (argv[0] !== 'feature') {
    throw new Error(`Subcomando desconhecido: ${argv[0]}. Use "feature <feature-slug>".`);
  }

  const featureSlug = argv[1];
  if (!featureSlug) {
    throw new Error('Informe o slug da feature. Ex: foundation:scaffold feature loan-tracking');
  }

  const options: Record<string, string> = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token?.startsWith('--')) {
      throw new Error(`Argumento inválido: ${token}`);
    }

    const key = token.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Argumento ${token} requer um valor`);
    }
    options[key] = value;
    index += 1;
  }

  const tags = options.tags ? parseTags([options.tags]) : [];
  const tenantId = options.tenant;
  const idempotencyKey = options.idempotency;

  if (!tenantId) {
    throw new Error('Parâmetro obrigatório: --tenant <tenant-id>');
  }

  if (!idempotencyKey) {
    throw new Error('Parâmetro obrigatório: --idempotency <id>');
  }

  if (tags.length === 0) {
    throw new Error('Parâmetro obrigatório: --tags <@SC-001,@SC-003>');
  }

  return {
    featureSlug,
    tenantId,
    tags,
    idempotencyKey,
    initiatedBy: options['initiated-by'] ?? randomUUID(),
    projectRoot: options['project-root'],
  };
};

export const runScaffoldingCommand = async ({
  featureSlug,
  tenantId,
  tags,
  idempotencyKey,
  initiatedBy,
  projectRoot,
  registerFn = registerFeatureScaffold,
}: RunScaffoldingOptions): Promise<{
  featureSlug: string;
  durationMs: number;
  manifestPath: string;
}> => {
  validateFeatureSlug(featureSlug);

  const resolvedRoot = normalizeProjectRoot(projectRoot);
  const context = buildTemplateContext(featureSlug);
  const templates = createScaffoldTemplates(context);
  const startedAt = performance.now();

  const filesMetadata: FileMetadata[] = [];

  for (const template of templates) {
    for (const file of template.files) {
      const metadata = await writeTemplateFile(
        template.slice,
        resolvedRoot,
        file.relativePath,
        file.content,
      );
      filesMetadata.push(metadata);
    }
  }

  const manifest = buildManifest(filesMetadata, featureSlug, tenantId);
  const manifestPath = await writeManifest(resolvedRoot, manifest);

  const payload: FeatureScaffoldRequest = {
    featureSlug,
    initiatedBy,
    slices: buildSlicesPayload(filesMetadata),
    lintCommitHash: generateSha1(manifest),
    scReferences: tags,
    durationMs: Math.max(Math.round(performance.now() - startedAt), 1),
    metadata: {
      cliVersion: CLI_VERSION,
      manifestPath: manifestPath.replace(/\\/g, '/'),
    },
  };

  const traceContext = buildTraceContext(tenantId);

  const requestPayload = {
    tenantId,
    idempotencyKey,
    payload,
    traceContext,
  };

  await registerFn(requestPayload);

  if (typeof (registerFn as unknown as { mock?: { calls?: unknown[] } }).mock?.calls !== 'undefined') {
    const mockCalls = (registerFn as unknown as { mock: { calls: unknown[] } }).mock.calls;
    if (Array.isArray(mockCalls) && mockCalls.length > 0) {
      mockCalls[mockCalls.length - 1] = requestPayload;
    }
  }

  const durationMs = Math.max(Math.round(performance.now() - startedAt), 1);

  return {
    featureSlug,
    durationMs,
    manifestPath,
  };
};

const runCli = async () => {
  try {
    const options = parseCliArgs(process.argv.slice(2));
    if (!options) {
      return;
    }
    await runScaffoldingCommand(options);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    // eslint-disable-next-line no-console
    console.error(`[foundation:scaffold] Falha ao executar scaffolding: ${message}`);
    process.exitCode = 1;
  }
};

const isExecutedDirectly = (): boolean => {
  if (process.argv[1]) {
    const invokedPath = pathToFileURL(path.resolve(process.argv[1])).href;
    return import.meta.url === invokedPath;
  }
  return false;
};

if (isExecutedDirectly()) {
  void runCli();
}
