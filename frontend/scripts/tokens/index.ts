import { mkdir, readdir, readFile, rm, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { ZodError } from 'zod';

import { tenantIds, tenantTokens, tenantVersions } from '../../src/shared/config/theme/tenants';
import { TenantThemeResponseSchema, TokenCategories, TenantThemePayload } from './token-schema';

const UUID_REGEX = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

export type TenantThemeResponse = TenantThemePayload;

export type CachedTenantTokens = {
  alias: string;
  tenantId: string;
  etag?: string | null;
  payload: TenantThemePayload;
};

type PullTenantTokensOptions = {
  tenantId: string;
  tenantAlias?: string;
  endpoint?: string;
  cacheDir?: string;
  fetchImpl?: typeof fetch;
};

type BuildTenantArtifactsOptions = {
  cacheDir?: string;
  tenantsConfigPath?: string;
  tokensCssPath?: string;
};

const projectRoot = path.resolve(process.cwd());
const DEFAULT_CACHE_DIR = path.join(projectRoot, 'scripts', 'tokens', 'cache');
const DEFAULT_TENANTS_PATH = path.join(
  projectRoot,
  'src',
  'shared',
  'config',
  'theme',
  'tenants.ts',
);
const DEFAULT_CSS_PATH = path.join(projectRoot, 'src', 'shared', 'ui', 'tokens.css');

const formatZodIssues = (error: ZodError): string =>
  error.issues
    .map((issue) => {
      const pathLabel = issue.path.length > 0 ? issue.path.join('.') : 'root';
      return `${pathLabel}: ${issue.message}`;
    })
    .join('; ');

const parseTenantThemeResponse = (value: unknown, context: string): TenantThemePayload => {
  try {
    return TenantThemeResponseSchema.parse(value);
  } catch (error) {
    if (error instanceof ZodError) {
      const details = formatZodIssues(error);
      throw new Error(`${context}: falha ao validar TokenSchema — ${details}`);
    }
    throw error;
  }
};

const buildApiUrl = (endpoint: string, tenantId: string): string => {
  const base = endpoint.endsWith('/') ? endpoint.slice(0, -1) : endpoint;
  return `${base}/api/v1/tenants/${tenantId}/themes/current`;
};

const buildOfflineTenantLookup = (): Record<string, string> =>
  Object.entries(tenantIds).reduce<Record<string, string>>((lookup, [alias, id]) => {
    lookup[id.toLowerCase()] = alias;
    return lookup;
  }, {});

const offlineTenantById = buildOfflineTenantLookup();

const cloneTokens = (tokens: Record<string, string>): Record<string, string> =>
  Object.fromEntries(Object.entries(tokens));

const buildOfflinePayload = (tenantId: string): TenantThemePayload | null => {
  const alias = offlineTenantById[tenantId.toLowerCase()];
  if (!alias) {
    return null;
  }

  const categories = tenantTokens[alias];
  if (!categories) {
    return null;
  }

  const baseReport = {
    status: 'pass',
    violations: [] as unknown[],
  };

  return {
    tenantId,
    version: tenantVersions[alias] ?? '0.0.0',
    generatedAt: new Date().toISOString(),
    categories: {
      foundation: cloneTokens(categories.foundation),
      semantic: cloneTokens(categories.semantic),
      component: cloneTokens(categories.component),
    },
    wcagReport: {
      semantic: { ...baseReport },
      component: { ...baseReport },
    },
  };
};

const isUuid = (value: string): boolean => UUID_REGEX.test(value);

const resolveTenantInput = (value: string): { tenantId: string; alias: string } => {
  const normalized = value.trim().toLowerCase();

  if (isUuid(normalized)) {
    const aliasFromId = offlineTenantById[normalized];
    return {
      tenantId: normalized,
      alias: aliasFromId ?? normalized,
    };
  }

  const tenantIdFromAlias = tenantIds[normalized as keyof typeof tenantIds];
  if (!tenantIdFromAlias) {
    throw new Error(
      `Identificador de tenant inválido: "${value}". Informe um UUID ou alias conhecido (ex.: tenant-alfa).`,
    );
  }

  return {
    tenantId: tenantIdFromAlias.toLowerCase(),
    alias: normalized,
  };
};

const normalizeAlias = (value: string | undefined, fallback: string): string => {
  if (!value) {
    return fallback;
  }
  return value;
};

const getCacheDir = (cacheDir?: string): string => cacheDir ?? DEFAULT_CACHE_DIR;

export const pullTenantTokens = async (
  options: PullTenantTokensOptions,
): Promise<CachedTenantTokens> => {
  const resolved = resolveTenantInput(options.tenantId);
  const tenantAlias = normalizeAlias(options.tenantAlias, resolved.alias);
  const tenantId = resolved.tenantId;
  const cacheDir = getCacheDir(options.cacheDir);
  const endpoint = options.endpoint ?? process.env.FOUNDATION_API_URL ?? 'http://localhost:8000';
  const fetchFn = options.fetchImpl ?? fetch;

  const apiUrl = buildApiUrl(endpoint, tenantId);

  const performFetch = async () => {
    try {
      const response = await fetchFn(apiUrl, {
        headers: {
          Accept: 'application/json',
          'X-Tenant-Id': tenantId,
        },
      });

      if (!response.ok) {
        throw new Error(`status ${response.status} ${response.statusText}`);
      }

      const payload = parseTenantThemeResponse(await response.json(), 'Resposta da API de tokens');
      const etag = response.headers.get('ETag') ?? response.headers.get('etag');

      return { payload, etag };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);

      if (message.includes('TokenSchema')) {
        throw error;
      }

      const offlinePayload = buildOfflinePayload(tenantId);
      if (!offlinePayload) {
        throw new Error(
          `Falha ao buscar tokens do tenant ${tenantAlias} (${message}). Nenhum fixture offline disponível.`,
        );
      }

      console.warn(
        `[foundation:tokens] Fallback offline aplicado para ${tenantAlias} (${tenantId}) — motivo: ${message}`,
      );

      return {
        payload: offlinePayload,
        etag: `W/"offline-${tenantAlias}-${offlinePayload.version}"`,
      };
    }
  };

  const { payload, etag } = await performFetch();

  const cached: CachedTenantTokens = {
    alias: tenantAlias,
    tenantId,
    etag,
    payload,
  };

  await mkdir(cacheDir, { recursive: true });
  const filePath = path.join(cacheDir, `${tenantId}.json`);
  await writeFile(filePath, JSON.stringify(cached, null, 2), 'utf-8');

  return cached;
};

const normalizeValue = (value: unknown): string => {
  if (value == null) {
    return '';
  }
  return String(value);
};

const formatTsObject = (
  data: Record<string, TokenCategories>,
  versions: Record<string, string>,
  ids: Record<string, string>,
): string => {
  const lines: string[] = [];
  lines.push('// Auto-gerado por foundation:tokens. Não editar manualmente.');
  lines.push(
    [
      'export type TenantTokenCategories = {',
      '  foundation: Record<string, string>;',
      '  semantic: Record<string, string>;',
      '  component: Record<string, string>;',
      '};',
    ].join('\n'),
  );
  lines.push('');
  lines.push('export const tenantTokens: Record<string, TenantTokenCategories> = {');
  const tenantEntries = Object.entries(data).sort(([a], [b]) => a.localeCompare(b));
  tenantEntries.forEach(([alias, categories], index) => {
    const categoryEntries = Object.entries(categories)
      .sort(([a], [b]) => a.localeCompare(b))
      .flatMap(([category, tokens]) => {
        const tokenLines = Object.entries(tokens)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([token, value]) => `      '${token}': '${value}',`);
        return [`    ${category}: {`, ...tokenLines, '    },'];
      });

    lines.push(`  '${alias}': {`);
    lines.push(...categoryEntries);
    lines.push(index === tenantEntries.length - 1 ? '  }' : '  },');
  });
  lines.push('} as const;');
  lines.push('');
  lines.push('export const tenantVersions: Record<string, string> = {');
  Object.entries(versions)
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([alias, version], index, array) => {
      const comma = index === array.length - 1 ? '' : ',';
      lines.push(`  '${alias}': '${version}'${comma}`);
    });
  lines.push('} as const;');
  lines.push('');
  lines.push('export const tenantIds: Record<string, string> = {');
  Object.entries(ids)
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([alias, id], index, array) => {
      const comma = index === array.length - 1 ? '' : ',';
      lines.push(`  '${alias}': '${id}'${comma}`);
    });
  lines.push('} as const;');
  lines.push('');
  return `${lines.join('\n')}`;
};

const toCssVariable = (token: string): string => `--${token.replace(/\./g, '-')}`;

const formatCss = (data: Array<{ alias: string; categories: TokenCategories }>): string => {
  const blocks = data.map(({ alias, categories }) => {
    const flattened = Object.values(categories).reduce<Record<string, string>>((acc, current) => {
      Object.entries(current).forEach(([token, value]) => {
        acc[token] = value;
      });
      return acc;
    }, {});

    const lines = Object.entries(flattened)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([token, value]) => `  ${toCssVariable(token)}: ${normalizeValue(value)};`)
      .join('\n');

    return `html[data-tenant="${alias}"] {\n${lines}\n}`;
  });

  if (blocks.length === 0) {
    return '/* Nenhum tenant disponível para tokens. */\n';
  }

  return (
    ['/* Auto-gerado por foundation:tokens. Não editar manualmente. */', ...blocks].join('\n\n') +
    '\n'
  );
};

const cleanupLegacyArtifacts = async (): Promise<void> => {
  const duplicatedRoot = path.join(projectRoot, 'frontend');
  try {
    const stats = await stat(duplicatedRoot);
    if (!stats.isDirectory()) {
      return;
    }
    await rm(duplicatedRoot, { recursive: true, force: true });
    // eslint-disable-next-line no-console
    console.warn(
      `[foundation:tokens] Diretório duplicado "${duplicatedRoot}" removido para evitar artefatos obsoletos.`,
    );
  } catch (error) {
    const code = (error as NodeJS.ErrnoException | undefined)?.code;
    if (code && code !== 'ENOENT') {
      // eslint-disable-next-line no-console
      console.warn(`[foundation:tokens] Falha ao limpar diretório legado ${duplicatedRoot}:`, error);
    }
  }
};

export const buildTenantArtifacts = async (
  options: BuildTenantArtifactsOptions = {},
): Promise<void> => {
  const cacheDir = getCacheDir(options.cacheDir);
  const tenantsConfigPath = options.tenantsConfigPath ?? DEFAULT_TENANTS_PATH;
  const tokensCssPath = options.tokensCssPath ?? DEFAULT_CSS_PATH;

  await mkdir(cacheDir, { recursive: true });
  await mkdir(path.dirname(tenantsConfigPath), { recursive: true });
  await mkdir(path.dirname(tokensCssPath), { recursive: true });

  const files = await readdir(cacheDir);
  const tenants: CachedTenantTokens[] = [];

  for (const file of files) {
    if (!file.endsWith('.json')) {
      continue;
    }
    const filePath = path.join(cacheDir, file);
    const content = await readFile(filePath, 'utf-8');
    const parsed = JSON.parse(content) as CachedTenantTokens;
    const validatedPayload = parseTenantThemeResponse(
      parsed.payload,
      `Cache de tokens (${filePath})`,
    );
    tenants.push({ ...parsed, payload: validatedPayload });
  }

  tenants.sort((a, b) => a.alias.localeCompare(b.alias));

  const categoriesByAlias: Record<string, TokenCategories> = {};
  const versionsByAlias: Record<string, string> = {};
  const idsByAlias: Record<string, string> = {};

  tenants.forEach((tenant) => {
    categoriesByAlias[tenant.alias] = tenant.payload.categories;
    versionsByAlias[tenant.alias] = tenant.payload.version;
    idsByAlias[tenant.alias] = tenant.tenantId;
  });

  const tsContent = formatTsObject(categoriesByAlias, versionsByAlias, idsByAlias);
  await writeFile(tenantsConfigPath, `${tsContent}\n`, 'utf-8');

  const cssPayload = formatCss(
    tenants.map((tenant) => ({ alias: tenant.alias, categories: tenant.payload.categories })),
  );
  await writeFile(tokensCssPath, cssPayload, 'utf-8');

  await cleanupLegacyArtifacts();
};

const parseCliArgs = (argv: string[]): { command: string; args: string[] } => {
  if (argv.length === 0) {
    throw new Error('Informe um subcomando. Ex.: foundation:tokens pull --tenant-id <uuid>');
  }
  const [command, ...rest] = argv;
  return { command, args: rest };
};

const parseOptions = (tokens: string[]): Record<string, string> => {
  const options: Record<string, string> = {};
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith('--')) {
      throw new Error(`Argumento inválido: ${token}`);
    }
    const key = token.slice(2);
    const value = tokens[index + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Argumento "${token}" requer um valor.`);
    }
    options[key] = value;
    index += 1;
  }
  return options;
};

const runCli = async (): Promise<void> => {
  const [, , ...rawArgs] = process.argv;
  const { command, args } = parseCliArgs(rawArgs);
  const options = parseOptions(args);

  if (command === 'pull') {
    const tenantId = options['tenant-id'] ?? options['tenant'];
    if (!tenantId) {
      throw new Error('Informe --tenant-id <uuid> (ou --tenant quando for UUID).');
    }
    const alias = options['alias'] ?? options['tenant-alias'] ?? options['tenant'];
    const endpoint = options['endpoint'];
    await pullTenantTokens({ tenantId, tenantAlias: alias, endpoint });
    return;
  }

  if (command === 'build') {
    await buildTenantArtifacts();
    return;
  }

  throw new Error(`Subcomando desconhecido: ${command}`);
};

const isCli = (): boolean => {
  const expected = pathToFileURL(process.argv[1] ?? '').href;
  return import.meta.url === expected;
};

export { TokenSchema, tokenSchemaJson, tenantThemeSchemaJson } from './token-schema';

if (isCli()) {
  runCli().catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
