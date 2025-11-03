import { readFileSync, writeFileSync } from 'node:fs';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import process from 'node:process';

import { tenantTokens } from '../../src/shared/config/theme/tenants';

type StoryIndexEntry = {
  id: string;
  title: string;
  name: string;
  parameters?: Record<string, unknown>;
};

type StoryIndexFile = {
  stories: Record<string, StoryIndexEntry>;
};

type CLIOptions = {
  storiesPath: string;
  minCoverage: number;
  expectedTenants: string[];
  outputFile?: string;
  verbose: boolean;
};

type CoverageResult = {
  tenant: string;
  covered: number;
  total: number;
  percentage: number;
  missingComponents: string[];
};

const DEFAULT_MIN_COVERAGE = 95;

const parseArgs = (argv: string[]): CLIOptions => {
  const options: CLIOptions = {
    storiesPath: 'storybook-static/stories.json',
    minCoverage: DEFAULT_MIN_COVERAGE,
    expectedTenants: Object.keys(tenantTokens),
    verbose: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--stories':
      case '--stories-path': {
        options.storiesPath = argv[index + 1] ?? options.storiesPath;
        index += 1;
        break;
      }
      case '--min':
      case '--min-coverage': {
        const value = Number.parseFloat(argv[index + 1] ?? '');
        if (!Number.isNaN(value)) {
          options.minCoverage = value;
        }
        index += 1;
        break;
      }
      case '--tenants': {
        const value = argv[index + 1];
        if (value) {
          options.expectedTenants = value
            .split(',')
            .map((tenant) => tenant.trim())
            .filter(Boolean);
        }
        index += 1;
        break;
      }
      case '--output':
      case '--output-file': {
        options.outputFile = argv[index + 1] ?? undefined;
        index += 1;
        break;
      }
      case '--verbose': {
        options.verbose = true;
        break;
      }
      default:
        break;
    }
  }

  if (process.env.CHROMATIC_MIN_COVERAGE) {
    const value = Number.parseFloat(process.env.CHROMATIC_MIN_COVERAGE);
    if (!Number.isNaN(value)) {
      options.minCoverage = value;
    }
  }

  if (process.env.CHROMATIC_TENANTS) {
    const tenants = process.env.CHROMATIC_TENANTS.split(',')
      .map((tenant) => tenant.trim())
      .filter(Boolean);

    if (tenants.length > 0) {
      options.expectedTenants = tenants;
    }
  }

  options.storiesPath = resolve(process.cwd(), options.storiesPath);

  return options;
};

const isChromaticEnabled = (entry: StoryIndexEntry): boolean => {
  const chromaticParameters = (
    entry.parameters as Record<string, unknown> | undefined
  )?.chromatic as unknown;

  if (typeof chromaticParameters === 'boolean') {
    return chromaticParameters;
  }

  if (chromaticParameters && typeof chromaticParameters === 'object') {
    const disableSnapshot = (chromaticParameters as Record<string, unknown>).disableSnapshot;
    if (typeof disableSnapshot === 'boolean') {
      return !disableSnapshot;
    }
  }

  return true;
};

const deriveTenantsFromId = (id: string): string[] => {
  const match = id.match(/--tenant-([a-z0-9-]+)/i);
  if (match && match[1]) return [match[1]];
  return [];
};

const extractTenantsFromEntry = (
  entry: StoryIndexEntry,
  fallbackTenant: string,
): string[] => {
  const params = entry.parameters as Record<string, unknown> | undefined;
  const rawTenant = params?.tenant as unknown;

  if (typeof rawTenant === 'string') {
    return [rawTenant];
  }

  if (Array.isArray(rawTenant)) {
    return rawTenant.filter((element): element is string => typeof element === 'string');
  }

  const tenantsFromParameters = params?.tenants as unknown;

  if (Array.isArray(tenantsFromParameters)) {
    return tenantsFromParameters.filter((element): element is string => typeof element === 'string');
  }

  // tentar inferir do id (ex.: ...--tenant-alfa)
  const fromId = deriveTenantsFromId(entry.id);
  if (fromId.length > 0) return fromId;
  return [fallbackTenant];
};

const computeCoverage = ({
  storiesPath,
  expectedTenants,
  minCoverage,
  outputFile,
  verbose,
}: CLIOptions): CoverageResult[] => {
  let effectivePath = storiesPath;
  if (!existsSync(effectivePath)) {
    // fallback para index.json do Storybook 8
    const alt = resolve(process.cwd(), 'storybook-static/index.json');
    if (!existsSync(alt)) {
      throw new Error(
        `Arquivo stories.json não encontrado em ${storiesPath} nem index.json em ${alt}. Execute o build do Storybook antes de validar a cobertura.`,
      );
    }
    effectivePath = alt;
  }

  const raw = JSON.parse(readFileSync(effectivePath, 'utf-8')) as
    | StoryIndexFile
    | { entries: Record<string, { id: string; title: string; name: string }> };

  let entries: StoryIndexEntry[] = [];
  if ((raw as StoryIndexFile).stories) {
    entries = Object.values((raw as StoryIndexFile).stories);
  } else if ((raw as any).entries) {
    const map = (raw as any).entries as Record<
      string,
      { id: string; title: string; name: string }
    >;
    entries = Object.values(map).map((e) => ({ id: e.id, title: e.title, name: e.name }));
  }

  if (entries.length === 0) {
    throw new Error('Nenhuma story encontrada no stories.json. Verifique a configuração do Storybook.');
  }

  const fallbackTenant =
    process.env.TENANT_DEFAULT && expectedTenants.includes(process.env.TENANT_DEFAULT)
      ? process.env.TENANT_DEFAULT
      : expectedTenants[0];

  const components = new Set<string>();
  const coverageByTenant = new Map<string, Set<string>>();

  for (const entry of entries) {
    if (!isChromaticEnabled(entry)) {
      continue;
    }

    components.add(entry.title);
    const tenants = extractTenantsFromEntry(entry, fallbackTenant);

    for (const tenant of tenants) {
      if (!coverageByTenant.has(tenant)) {
        coverageByTenant.set(tenant, new Set());
      }
      coverageByTenant.get(tenant)?.add(entry.title);
    }
  }

  const totalComponents = components.size;

  if (totalComponents === 0) {
    throw new Error('Nenhum componente disponível para cálculo de cobertura visual.');
  }

  const results: CoverageResult[] = expectedTenants.map((tenant) => {
    const coveredComponents = coverageByTenant.get(tenant) ?? new Set<string>();
    const coverage = (coveredComponents.size / totalComponents) * 100;
    const missingComponents = [...components].filter(
      (component) => !coveredComponents.has(component),
    );

    return {
      tenant,
      covered: coveredComponents.size,
      total: totalComponents,
      percentage: Number(coverage.toFixed(2)),
      missingComponents,
    };
  });

  if (outputFile) {
    const payload = {
      generatedAt: new Date().toISOString(),
      minCoverage,
      results,
    };
    writeFileSync(resolve(process.cwd(), outputFile), JSON.stringify(payload, null, 2));
  }

  if (verbose) {
    const header = ['Tenant', 'Cobertos', 'Total', 'Cobertura (%)'];
    const rows = results.map((result) => [
      result.tenant,
      String(result.covered),
      String(result.total),
      result.percentage.toFixed(2),
    ]);

    const table = [header, ...rows]
      .map((row) => row.map((col) => col.padEnd(16, ' ')).join(' | '))
      .join('\n');

    // eslint-disable-next-line no-console
    console.log(table);
  }

  return results;
};

const main = () => {
  const options = parseArgs(process.argv.slice(2));

  try {
    const results = computeCoverage(options);

    const failures = results.filter((result) => result.percentage < options.minCoverage);

    if (failures.length > 0) {
      for (const failure of failures) {
        const missingList =
          failure.missingComponents.length > 0
            ? ` Componentes faltantes: ${failure.missingComponents.join(', ')}.`
            : '';
        // eslint-disable-next-line no-console
        console.error(
          `Cobertura visual para ${failure.tenant} abaixo do mínimo (${failure.percentage.toFixed(2)}% < ${options.minCoverage}%).${missingList}`,
        );
      }
      process.exit(1);
    }

    if (options.verbose) {
      // eslint-disable-next-line no-console
      console.log(
        `Cobertura visual atendida: todas as variações possuem >= ${options.minCoverage}% de componentes registrados.`,
      );
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error(
      error instanceof Error ? error.message : 'Falha desconhecida ao validar cobertura visual.',
    );
    process.exit(1);
  }
};

main();
