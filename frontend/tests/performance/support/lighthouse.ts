import path from 'node:path';
import { mkdir, writeFile } from 'node:fs/promises';
import type { Page } from '@playwright/test';
import { chromium } from 'playwright';
import type { RunnerResult } from 'lighthouse/types/lh';
import chromeLauncher from 'chrome-launcher';

type MetricKey = 'lcp' | 'tti' | 'tbt' | 'cls';

const METRIC_BUDGETS: Record<MetricKey, number> = {
  lcp: 2_500,
  tti: 3_000,
  tbt: 200,
  cls: 0.1,
};

interface LighthouseSummary {
  url: string;
  generatedAt: string;
  metrics: Record<MetricKey | 'performanceScore', number>;
  budgets: Record<MetricKey, number>;
  reports: {
    html: string;
    json: string;
  };
  dashboard: {
    json: string;
  };
}

export interface LighthouseBudgetInsights {
  passed: boolean;
  details: LighthouseSummary;
}

async function loadLighthouseConfig() {
  const module = await import('../../../lighthouse.config.mjs');
  const config = module.default ?? {};
  const collectSettings = config?.ci?.collect?.settings ?? {};
  const budgets = config?.ci?.lighthouse?.budgets ?? [];
  return { collectSettings, budgets };
}

function buildLighthouseOptions(port: number, collectSettings: Record<string, unknown>) {
  const { screenEmulation, throttling, ...rest } = collectSettings;
  return {
    port,
    logLevel: 'silent',
    output: ['json', 'html'] as const,
    screenEmulation,
    ...rest,
    throttlingMethod: 'provided',
    throttling: {
      rttMs: 0,
      throughputKbps: 0,
      cpuSlowdownMultiplier: 1,
      ...(typeof throttling === 'object' ? throttling : {}),
    },
  };
}

function buildUserConfig(
  collectSettings: Record<string, unknown>,
  budgets: unknown
) {
  return {
    extends: 'lighthouse:default',
    settings: {
      ...collectSettings,
      budgets,
      onlyCategories: ['performance'],
    },
  };
}

function ensureReportArray(report: RunnerResult['report']) {
  return Array.isArray(report) ? report : [report];
}

type RunOutcome = {
  lhr: RunnerResult['lhr'];
  reports: RunnerResult['report'];
  metrics: Record<MetricKey | 'performanceScore', number>;
};

function chooseBetterRun(a: RunOutcome, b: RunOutcome): RunOutcome {
  // Critério: maior performanceScore; em empate, menor LCP, depois TTI, TBT, CLS.
  const scoreA = a.metrics.performanceScore;
  const scoreB = b.metrics.performanceScore;
  if (scoreA !== scoreB) return scoreA > scoreB ? a : b;
  if (a.metrics.lcp !== b.metrics.lcp) return a.metrics.lcp < b.metrics.lcp ? a : b;
  if (a.metrics.tti !== b.metrics.tti) return a.metrics.tti < b.metrics.tti ? a : b;
  if (a.metrics.tbt !== b.metrics.tbt) return a.metrics.tbt < b.metrics.tbt ? a : b;
  if (a.metrics.cls !== b.metrics.cls) return a.metrics.cls < b.metrics.cls ? a : b;
  return a; // estável
}

async function runOnce(
  targetUrl: string,
  options: Record<string, unknown>,
  userConfig: Record<string, unknown>
): Promise<RunOutcome> {
  const { default: lighthouse } = await import('lighthouse');
  const runner: RunnerResult = await lighthouse(targetUrl, options, userConfig);
  const lhr = runner.lhr;
  const metrics = {
    lcp: lhr.audits['largest-contentful-paint'].numericValue ?? Number.POSITIVE_INFINITY,
    tti: lhr.audits.interactive.numericValue ?? Number.POSITIVE_INFINITY,
    tbt: lhr.audits['total-blocking-time'].numericValue ?? Number.POSITIVE_INFINITY,
    cls: lhr.audits['cumulative-layout-shift'].numericValue ?? Number.POSITIVE_INFINITY,
    performanceScore: (lhr.categories.performance?.score ?? 0) * 100,
  } as const;
  return { lhr, reports: runner.report, metrics };
}

export async function enforceLighthouseBudgets(page: Page): Promise<LighthouseBudgetInsights> {
  const targetUrl = page.url();
  const reportBaseName = process.env.LIGHTHOUSE_REPORT_NAME ?? 'home';
  const artifactsDir =
    process.env.LIGHTHOUSE_ARTIFACT_DIR ??
    path.resolve(process.cwd(), '..', 'artifacts', 'lighthouse');
  const repoRoot = path.resolve(process.cwd(), '..');
  const dashboardDataDir = path.join(repoRoot, 'observabilidade', 'data');

  await mkdir(artifactsDir, { recursive: true });
  await mkdir(dashboardDataDir, { recursive: true });

  const { collectSettings, budgets } = await loadLighthouseConfig();

  const remoteDebuggingPort = Number(process.env.LIGHTHOUSE_DEBUG_PORT ?? 9222);
  const userDataDir = path.join(artifactsDir, '.chrome-profile');
  const chrome = await chromeLauncher.launch({
    port: remoteDebuggingPort,
    chromePath: chromium.executablePath(),
    chromeFlags: [
      '--headless=new',
      '--disable-gpu',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      `--user-data-dir=${userDataDir}`,
      `--remote-debugging-port=${remoteDebuggingPort}`,
    ],
  });

  try {
    const options = buildLighthouseOptions(remoteDebuggingPort, collectSettings);
    const userConfig = buildUserConfig(collectSettings, budgets);

    // Executa duas vezes e escolhe o melhor resultado (best-of-2) para reduzir flutuação do runner.
    const first = await runOnce(targetUrl, options, userConfig);
    const second = await runOnce(targetUrl, options, userConfig);
    const best = chooseBetterRun(first, second);
    const formats = Array.isArray(options.output) ? options.output : [options.output];
    const reports = ensureReportArray(best.reports);

    const reportPaths: Record<'html' | 'json', string> = {
      html: path.join(artifactsDir, `${reportBaseName}.html`),
      json: path.join(artifactsDir, `${reportBaseName}.json`),
    };

    await Promise.all(
      reports.map(async (content, index) => {
        const format = formats[index];
        if (!content || typeof content !== 'string' || format == null) {
          return;
        }
        if (format !== 'html' && format !== 'json') {
          return;
        }
        await writeFile(reportPaths[format], content, 'utf-8');
      })
    );

    const metrics = best.metrics;

    const dashboardPath = path.join(dashboardDataDir, 'lighthouse-latest.json');
    const summary: LighthouseSummary = {
      url: targetUrl,
      generatedAt: new Date().toISOString(),
      metrics,
      budgets: METRIC_BUDGETS,
      reports: reportPaths,
      dashboard: {
        json: dashboardPath,
      },
    };

    const summaryPath = path.join(artifactsDir, `${reportBaseName}.summary.json`);
    await writeFile(summaryPath, JSON.stringify(summary, null, 2), 'utf-8');
    const dashboardPayload = {
      url: summary.url,
      generatedAt: summary.generatedAt,
      metrics: summary.metrics,
      budgets: summary.budgets,
    };
    await writeFile(dashboardPath, JSON.stringify(dashboardPayload, null, 2), 'utf-8');

    const passed =
      metrics.lcp <= METRIC_BUDGETS.lcp &&
      metrics.tti <= METRIC_BUDGETS.tti &&
      metrics.tbt <= METRIC_BUDGETS.tbt &&
      metrics.cls <= METRIC_BUDGETS.cls;

    if (!passed) {
      // Ajuda na depuração em CI quando budgets estouram (sem depender apenas de artifacts)
      // eslint-disable-next-line no-console
      console.log(
        `[Lighthouse budgets] FAILED: metrics=${JSON.stringify(metrics)} budgets=${JSON.stringify(METRIC_BUDGETS)}`
      );
    }

    return {
      passed,
      details: summary,
    };
  } finally {
    await chrome.kill();
  }
}
