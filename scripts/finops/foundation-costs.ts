/* eslint-disable @typescript-eslint/no-explicit-any */
export {};

const fs = require('node:fs/promises');
const path = require('node:path');

type UsageRecord = {
  tenant: string;
  feature?: string;
  runs: number;
  cost: number;
  currency?: string;
  timestamp?: string;
};

type SourceConfig = {
  name: string;
  source?: string;
  budget?: number;
  warnPercent?: number;
  statusUrl?: string;
  fallbackFile?: string;
};

type CliOptions = {
  outputJson: string;
  outputProm: string;
  dryRun: boolean;
  chromaticSource?: string;
  lighthouseSource?: string;
  pipelinesSource?: string;
  chromaticBudget?: number;
  lighthouseBudget?: number;
  pipelinesBudget?: number;
  totalBudget?: number;
  warnPercent?: number;
};

type AggregatedTenant = {
  cost: number;
  runs: number;
  features: Record<string, { cost: number; runs: number }>;
};

type AggregatedTool = {
  tool: string;
  totalCost: number;
  currency: string;
  runs: number;
  tenants: Record<string, AggregatedTenant>;
  budget?: number;
  warnPercent: number;
};

type AggregatedReport = {
  generatedAt: string;
  totals: AggregatedTool[];
  totalBudget?: number;
  totalCost: number;
  budgetPercent?: number;
  alerts: string[];
};

const DEFAULT_WARN_PERCENT = 0.8;
const DEFAULT_OUTPUT_JSON = path.join('observabilidade', 'data', 'foundation-costs.json');
const DEFAULT_OUTPUT_PROM = path.join('observabilidade', 'data', 'foundation-costs.prom');
const FALLBACK_DATA_DIR = path.resolve(process.cwd(), 'scripts', 'finops', 'fixtures');

function parseArgs(): CliOptions {
  const argv = process.argv.slice(2);
  const options: CliOptions = {
    outputJson: DEFAULT_OUTPUT_JSON,
    outputProm: DEFAULT_OUTPUT_PROM,
    dryRun: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    switch (arg) {
      case '--output-json':
        if (next) {
          options.outputJson = next;
          index += 1;
        }
        break;
      case '--output-prom':
        if (next) {
          options.outputProm = next;
          index += 1;
        }
        break;
      case '--dry-run':
        options.dryRun = true;
        break;
      case '--chromatic':
        if (next) {
          options.chromaticSource = next;
          index += 1;
        }
        break;
      case '--lighthouse':
        if (next) {
          options.lighthouseSource = next;
          index += 1;
        }
        break;
      case '--pipelines':
        if (next) {
          options.pipelinesSource = next;
          index += 1;
        }
        break;
      case '--chromatic-budget':
        if (next) {
          options.chromaticBudget = Number(next);
          index += 1;
        }
        break;
      case '--lighthouse-budget':
        if (next) {
          options.lighthouseBudget = Number(next);
          index += 1;
        }
        break;
      case '--pipelines-budget':
        if (next) {
          options.pipelinesBudget = Number(next);
          index += 1;
        }
        break;
      case '--total-budget':
        if (next) {
          options.totalBudget = Number(next);
          index += 1;
        }
        break;
      case '--warn-percent':
        if (next) {
          options.warnPercent = Number(next);
          index += 1;
        }
        break;
      default:
        break;
    }
  }

  return options;
}

function readEnv(name: string): string | undefined {
  const value = process.env[name];
  if (!value || value.trim() === '') {
    return undefined;
  }
  return value.trim();
}

function parseBudget(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}

function parsePercent(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    return undefined;
  }
  if (parsed > 1) {
    return parsed / 100;
  }
  return parsed;
}

async function loadUsage(source?: string, fallbackFile?: string): Promise<UsageRecord[]> {
  if (!source && fallbackFile) {
    source = fallbackFile;
  }
  if (!source) {
    return [];
  }
  if (source.startsWith('http://') || source.startsWith('https://')) {
    try {
      const response = await fetch(source);
      if (!response.ok) {
        console.warn(`[foundation-costs] Falha ao obter ${source}: status ${response.status}`);
        return [];
      }
      return await response.json();
    } catch (error) {
      console.warn(`[foundation-costs] Erro de rede ao obter ${source}: ${(error as Error).message}`);
      return [];
    }
  }
  try {
    const raw = await fs.readFile(source, 'utf-8');
    return JSON.parse(raw);
  } catch (error) {
    console.warn(`[foundation-costs] Não foi possível ler ${source}: ${(error as Error).message}`);
    return [];
  }
}

function upsertTenant(
  tenants: Record<string, AggregatedTenant>,
  tenantKey: string,
  cost: number,
  runs: number,
  feature?: string,
) {
  if (!tenants[tenantKey]) {
    tenants[tenantKey] = { cost: 0, runs: 0, features: {} };
  }
  tenants[tenantKey].cost += cost;
  tenants[tenantKey].runs += runs;
  if (feature) {
    const featureKey = feature;
    if (!tenants[tenantKey].features[featureKey]) {
      tenants[tenantKey].features[featureKey] = { cost: 0, runs: 0 };
    }
    tenants[tenantKey].features[featureKey].cost += cost;
    tenants[tenantKey].features[featureKey].runs += runs;
  }
}

function aggregateUsage(
  name: string,
  records: UsageRecord[],
  defaultCurrency: string,
  budget: number | undefined,
  warnPercent: number,
): AggregatedTool {
  const tenants: Record<string, AggregatedTenant> = {};
  let totalCost = 0;
  let runs = 0;
  let currency = defaultCurrency;

  for (const record of records) {
    const cost = Number(record.cost) || 0;
    const currentRuns = Number(record.runs) || 0;
    totalCost += cost;
    runs += currentRuns;
    currency = record.currency || currency;
    const tenantKey = record.tenant || 'unknown';
    upsertTenant(tenants, tenantKey, cost, currentRuns, record.feature);
  }

  return {
    tool: name,
    totalCost,
    currency,
    runs,
    tenants,
    budget,
    warnPercent,
  };
}

function toPrometheus(report: AggregatedReport): string {
  const lines: string[] = [];

  lines.push('# HELP foundation_finops_cost_total Custo acumulado por ferramenta');
  lines.push('# TYPE foundation_finops_cost_total gauge');
  for (const total of report.totals) {
    const currencyLabel = total.currency || 'USD';
    lines.push(
      `foundation_finops_cost_total{tool="${total.tool}",currency="${currencyLabel}"} ${total.totalCost.toFixed(
        2,
      )}`,
    );
    for (const [tenant, stats] of Object.entries(total.tenants)) {
      lines.push(
        `foundation_finops_cost_by_tenant{tool="${total.tool}",tenant="${tenant}"} ${stats.cost.toFixed(2)}`,
      );
    }
  }

  lines.push('# HELP foundation_finops_runs_total Execuções por ferramenta');
  lines.push('# TYPE foundation_finops_runs_total counter');
  for (const total of report.totals) {
    lines.push(`foundation_finops_runs_total{tool="${total.tool}"} ${total.runs}`);
  }

  lines.push('# HELP foundation_finops_budget_consumed_percent Percentual consumido do orçamento');
  lines.push('# TYPE foundation_finops_budget_consumed_percent gauge');

  for (const total of report.totals) {
    if (total.budget && total.budget > 0) {
      const percent = total.totalCost / total.budget;
      lines.push(`foundation_finops_budget_consumed_percent{tool="${total.tool}"} ${(percent * 100).toFixed(2)}`);
    }
  }

  if (report.totalBudget && report.totalBudget > 0) {
    lines.push(
      `foundation_finops_budget_consumed_percent{tool="total"} ${((report.totalCost / report.totalBudget) * 100).toFixed(
        2,
      )}`,
    );
  }

  return `${lines.join('\n')}\n`;
}

async function ensureDir(filePath: string) {
  const dir = path.dirname(filePath);
  await fs.mkdir(dir, { recursive: true });
}

function buildSourceConfig(options: CliOptions): SourceConfig[] {
  return [
    {
      name: 'chromatic',
      source: options.chromaticSource || readEnv('FOUNDATION_FINOPS_CHROMATIC_SOURCE'),
      budget: options.chromaticBudget ?? parseBudget(readEnv('FOUNDATION_FINOPS_CHROMATIC_BUDGET')),
      warnPercent:
        options.warnPercent ??
        parsePercent(readEnv('FOUNDATION_FINOPS_WARN_PERCENT')) ??
        parsePercent(readEnv('FOUNDATION_FINOPS_CHROMATIC_WARN_PERCENT')) ??
        DEFAULT_WARN_PERCENT,
      statusUrl: readEnv('FOUNDATION_FINOPS_CHROMATIC_STATUS_URL'),
      fallbackFile: path.join(FALLBACK_DATA_DIR, 'chromatic.json'),
    },
    {
      name: 'lighthouse',
      source: options.lighthouseSource || readEnv('FOUNDATION_FINOPS_LIGHTHOUSE_SOURCE'),
      budget: options.lighthouseBudget ?? parseBudget(readEnv('FOUNDATION_FINOPS_LIGHTHOUSE_BUDGET')),
      warnPercent:
        options.warnPercent ??
        parsePercent(readEnv('FOUNDATION_FINOPS_WARN_PERCENT')) ??
        parsePercent(readEnv('FOUNDATION_FINOPS_LIGHTHOUSE_WARN_PERCENT')) ??
        DEFAULT_WARN_PERCENT,
      statusUrl: readEnv('FOUNDATION_FINOPS_LIGHTHOUSE_STATUS_URL'),
      fallbackFile: path.join(FALLBACK_DATA_DIR, 'lighthouse.json'),
    },
    {
      name: 'pipelines',
      source: options.pipelinesSource || readEnv('FOUNDATION_FINOPS_PIPELINES_SOURCE'),
      budget: options.pipelinesBudget ?? parseBudget(readEnv('FOUNDATION_FINOPS_PIPELINES_BUDGET')),
      warnPercent:
        options.warnPercent ??
        parsePercent(readEnv('FOUNDATION_FINOPS_WARN_PERCENT')) ??
        parsePercent(readEnv('FOUNDATION_FINOPS_PIPELINES_WARN_PERCENT')) ??
        DEFAULT_WARN_PERCENT,
      statusUrl: readEnv('FOUNDATION_FINOPS_PIPELINES_STATUS_URL'),
      fallbackFile: path.join(FALLBACK_DATA_DIR, 'pipelines.json'),
    },
  ];
}

async function checkServiceStatus(url?: string): Promise<'operational' | 'degraded' | 'outage' | 'unknown'> {
  if (!url) {
    return 'unknown';
  }
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return 'unknown';
    }
    const payload = await response.json();
    const status = (payload.status || payload.indicator || payload.state || '').toString().toLowerCase();
    if (status.includes('operational') || status === 'ok' || status === 'green') {
      return 'operational';
    }
    if (status.includes('major') || status.includes('critical') || status.includes('outage')) {
      return 'outage';
    }
    if (status.includes('minor') || status.includes('degraded') || status.includes('warning')) {
      return 'degraded';
    }
    return 'unknown';
  } catch (error) {
    console.warn(`[foundation-costs] Não foi possível consultar status ${url}: ${(error as Error).message}`);
    return 'unknown';
  }
}

async function main() {
  const options = parseArgs();
  const totalBudget =
    options.totalBudget ?? parseBudget(readEnv('FOUNDATION_FINOPS_TOTAL_BUDGET')) ?? undefined;
  const sources = buildSourceConfig(options);
  const totals: AggregatedTool[] = [];
  const alerts: string[] = [];

  for (const sourceConfig of sources) {
    const status = await checkServiceStatus(sourceConfig.statusUrl);
    if (status === 'outage') {
      alerts.push(`Serviço ${sourceConfig.name} reporta indisponibilidade na API de status.`);
    } else if (status === 'degraded') {
      alerts.push(`Serviço ${sourceConfig.name} reporta degradação na API de status.`);
    }

    const usage = await loadUsage(sourceConfig.source, sourceConfig.fallbackFile);
    if (usage.length === 0) {
      alerts.push(`Nenhum dado de custo encontrado para ${sourceConfig.name}.`);
    }

    const aggregated = aggregateUsage(
      sourceConfig.name,
      usage,
      readEnv('FOUNDATION_FINOPS_DEFAULT_CURRENCY') || 'USD',
      sourceConfig.budget,
      sourceConfig.warnPercent ?? DEFAULT_WARN_PERCENT,
    );

    if (aggregated.budget && aggregated.budget > 0) {
      const percent = aggregated.totalCost / aggregated.budget;
      if (percent >= 1) {
        alerts.push(
          `Custo de ${sourceConfig.name} excedeu o orçamento (${(percent * 100).toFixed(2)}%).`,
        );
      } else if (percent >= (sourceConfig.warnPercent ?? DEFAULT_WARN_PERCENT)) {
        alerts.push(
          `Custo de ${sourceConfig.name} consumiu ${(percent * 100).toFixed(2)}% do orçamento.`,
        );
      }
    }

    totals.push(aggregated);
  }

  const totalCost = totals.reduce((acc, item) => acc + item.totalCost, 0);
  const report: AggregatedReport = {
    generatedAt: new Date().toISOString(),
    totals,
    totalBudget,
    totalCost,
    budgetPercent: totalBudget && totalBudget > 0 ? totalCost / totalBudget : undefined,
    alerts,
  };

  const jsonContent = JSON.stringify(report, null, 2);
  const promContent = toPrometheus(report);

  if (!options.dryRun) {
    await ensureDir(options.outputJson);
    await ensureDir(options.outputProm);
    await fs.writeFile(options.outputJson, jsonContent);
    await fs.writeFile(options.outputProm, promContent);
  }

  console.log(jsonContent);

  if (report.budgetPercent && report.budgetPercent >= 1) {
    process.exit(2);
  }
}

main().catch((error) => {
  console.error('[foundation-costs] Erro inesperado', error);
  process.exit(1);
});
