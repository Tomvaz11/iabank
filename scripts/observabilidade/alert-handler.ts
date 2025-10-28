#!/usr/bin/env node

/* eslint-disable @typescript-eslint/no-var-requires */

declare function require(name: string): any;

const fs = require('fs/promises');
const path = require('path');

type CliOptions = {
  summary: string;
  output?: string;
  threshold: number;
  warning: number;
  duration?: string;
};

type K6Summary = {
  metrics?: {
    http_reqs?: { count?: number };
  };
  state?: {
    testRunDurationMs?: number;
  };
  options?: {
    summaryTrendStats?: string[];
  };
};

const DEFAULT_CRITICAL = Number(process.env.FOUNDATION_THROUGHPUT_CRITICAL || 45);
const DEFAULT_WARNING = Number(process.env.FOUNDATION_THROUGHPUT_WARNING || DEFAULT_CRITICAL * 0.9);

function parseArgs(): CliOptions {
  const argv = process.argv.slice(2);
  const parsed: Partial<CliOptions> = {
    threshold: DEFAULT_CRITICAL,
    warning: DEFAULT_WARNING,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    switch (arg) {
      case '--summary':
        if (!next) {
          throw new Error('Parâmetro --summary exige um caminho para o arquivo JSON exportado pelo k6.');
        }
        parsed.summary = next;
        index += 1;
        break;
      case '--output':
        if (!next) {
          throw new Error('Parâmetro --output exige um caminho para gravação do resultado.');
        }
        parsed.output = next;
        index += 1;
        break;
      case '--threshold':
        if (!next) {
          throw new Error('Parâmetro --threshold exige um valor numérico (requests/s).');
        }
        parsed.threshold = Number(next);
        index += 1;
        break;
      case '--warning':
        if (!next) {
          throw new Error('Parâmetro --warning exige um valor numérico (requests/s).');
        }
        parsed.warning = Number(next);
        index += 1;
        break;
      case '--duration':
        if (!next) {
          throw new Error('Parâmetro --duration exige uma duração (ex.: 30s).');
        }
        parsed.duration = next;
        index += 1;
        break;
      default:
        break;
    }
  }

  if (!parsed.summary) {
    throw new Error('--summary é obrigatório para avaliar o throughput.');
  }

  parsed.threshold = Number.isFinite(parsed.threshold as number) ? (parsed.threshold as number) : DEFAULT_CRITICAL;
  parsed.warning =
    Number.isFinite(parsed.warning as number) && (parsed.warning as number) > 0
      ? (parsed.warning as number)
      : Math.max(parsed.threshold * 0.9, 1);

  if ((parsed.warning as number) > (parsed.threshold as number)) {
    parsed.warning = Math.max((parsed.threshold as number) * 0.9, 1);
  }

  return parsed as CliOptions;
}

function parseDuration(value?: string | number | null): number {
  if (value === null || value === undefined) {
    return 0;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value / 1000;
  }
  const normalized = value.toString().trim();
  const match = /^(\d+)(ms|s|m|h)?$/i.exec(normalized);
  if (!match) {
    return 0;
  }
  const amount = Number(match[1]);
  const unit = (match[2] || 's').toLowerCase();
  switch (unit) {
    case 'ms':
      return amount / 1000;
    case 'm':
      return amount * 60;
    case 'h':
      return amount * 3600;
    default:
      return amount;
  }
}

async function loadSummary(filePath: string): Promise<K6Summary> {
  const raw = await fs.readFile(filePath, 'utf-8');
  try {
    return JSON.parse(raw) as K6Summary;
  } catch (error) {
    throw new Error(`Não foi possível interpretar ${filePath} como JSON: ${(error as Error).message}`);
  }
}

function computeDuration(summary: K6Summary, fallbackDuration: string | undefined): number {
  if (summary.state?.testRunDurationMs) {
    return Math.max(summary.state.testRunDurationMs / 1000, 0);
  }
  if (fallbackDuration) {
    return parseDuration(fallbackDuration);
  }
  return 0;
}

function computeStatus(throughput: number, warning: number, critical: number): 'ok' | 'warning' | 'critical' {
  if (throughput >= critical) {
    return 'ok';
  }
  if (throughput >= warning) {
    return 'warning';
  }
  return 'critical';
}

type EvaluationResult = {
  generatedAt: string;
  metric: {
    name: string;
    unit: string;
    value: number;
    totalRequests: number;
    durationSeconds: number;
  };
  status: 'ok' | 'warning' | 'critical';
  threshold: {
    warning: number;
    critical: number;
  };
  ticket: string | null;
  message: string;
  summaryPath: string;
};

async function ensureDirectory(targetPath: string) {
  await fs.mkdir(path.dirname(targetPath), { recursive: true });
}

async function main() {
  const options = parseArgs();
  const summary = await loadSummary(options.summary);
  const totalRequests = summary.metrics?.http_reqs?.count ?? 0;
  const durationSeconds = computeDuration(summary, options.duration);
  const throughput = durationSeconds > 0 ? totalRequests / durationSeconds : 0;
  const status = computeStatus(throughput, options.warning, options.threshold);

  const result: EvaluationResult = {
    generatedAt: new Date().toISOString(),
    metric: {
      name: 'foundation_api_throughput',
      unit: 'requests_per_second',
      value: Number.isFinite(throughput) ? Number(throughput.toFixed(2)) : 0,
      totalRequests,
      durationSeconds,
    },
    status,
    threshold: {
      warning: Number(options.warning.toFixed(2)),
      critical: Number(options.threshold.toFixed(2)),
    },
    ticket: status === 'ok' ? null : '@SC-001',
    message:
      status === 'ok'
        ? 'Throughput dentro do alvo estabelecido para SC-001.'
        : `Throughput ${throughput.toFixed(2)} rps abaixo do alvo crítico (${options.threshold} rps).`,
    summaryPath: options.summary,
  };

  const payload = `${JSON.stringify(result, null, 2)}\n`;

  if (options.output) {
    await ensureDirectory(options.output);
    await fs.writeFile(options.output, payload, 'utf-8');
    console.log(`[observabilidade] Resultado gravado em ${options.output}`);
  } else {
    console.log(payload);
  }
}

if (process.argv[1] && process.argv[1].includes('alert-handler')) {
  main().catch((error) => {
    console.error(`[observabilidade] Falha ao gerar alerta foundation_api_throughput: ${(error as Error).message}`);
    process.exit(1);
  });
}
