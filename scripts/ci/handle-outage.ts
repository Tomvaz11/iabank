/* eslint-disable @typescript-eslint/no-explicit-any */
export {};

const fs = require('node:fs/promises');
const path = require('node:path');

type ToolStatus = {
  name: string;
  job: string;
  status: string;
  statusUrl?: string;
  logPath?: string;
  failurePatterns?: string[];
  allowFailOpen?: boolean;
};

type OutageInput = {
  branch: string;
  eventName: string;
  runId: number;
  runUrl?: string;
  commit: string;
  prNumber?: number;
  repository: string;
  owner: string;
  githubToken?: string;
  otelEndpoint?: string;
  defaultTenant?: string;
  tools: ToolStatus[];
  releaseBranches?: string[];
};

type ToolEvaluation = {
  tool: string;
  job: string;
  status: string;
  outage: boolean;
  reason?: string;
  evidence?: string;
};

type ScriptResult = {
  generatedAt: string;
  branch: string;
  runId: number;
  runUrl?: string;
  commit: string;
  eventName: string;
  outages: ToolEvaluation[];
  failOpen: boolean;
};

const DEFAULT_RELEASE_BRANCHES = ['main', 'release/', 'hotfix/'];
const OUTAGE_PATTERNS = [
  'ECONNRESET',
  'ECONNREFUSED',
  'ETIMEDOUT',
  '522',
  '523',
  '504',
  '502',
  'service unavailable',
  'statuspage outage',
  'rate limit',
];

const DEFAULT_STATUS_URLS: Record<string, string> = {
  chromatic: 'https://status.chromatic.com/api/v2/status.json',
  lighthouse: 'https://www.googleapis.com/lighthouse/v1/status',
};

function parseArgs(): { inputPath?: string } {
  const argv = process.argv.slice(2);
  const options: { inputPath?: string } = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];
    if (arg === '--input' && next) {
      options.inputPath = next;
      index += 1;
    }
  }
  return options;
}

async function readJson(filePath: string): Promise<any> {
  const raw = await fs.readFile(filePath, 'utf-8');
  return JSON.parse(raw);
}

function normalizeStatus(status: string | undefined): string {
  if (!status) {
    return 'unknown';
  }
  return status.toString().toLowerCase();
}

async function readLogPatterns(logPath: string | undefined): Promise<boolean> {
  if (!logPath) {
    return false;
  }
  try {
    const raw = await fs.readFile(logPath, 'utf-8');
    const lower = raw.toLowerCase();
    return OUTAGE_PATTERNS.some((pattern) => lower.includes(pattern.toLowerCase()));
  } catch (error) {
    console.warn(`[ci-outage] Não foi possível ler log ${logPath}: ${(error as Error).message}`);
    return false;
  }
}

async function checkStatusPage(url?: string): Promise<'operational' | 'degraded' | 'outage' | 'unknown'> {
  if (!url) {
    return 'unknown';
  }
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return 'unknown';
    }
    const json = await response.json();
    const statusText =
      json?.status?.description ||
      json?.status?.indicator ||
      json?.status ||
      json?.indicator ||
      json?.state;
    const normalized = normalizeStatus(statusText);
    if (normalized.includes('operational') || normalized === 'ok') {
      return 'operational';
    }
    if (normalized.includes('outage') || normalized.includes('major')) {
      return 'outage';
    }
    if (normalized.includes('minor') || normalized.includes('degraded')) {
      return 'degraded';
    }
    return 'unknown';
  } catch (error) {
    console.warn(`[ci-outage] Falha ao consultar ${url}: ${(error as Error).message}`);
    return 'unknown';
  }
}

function buildInputFromEnv(): OutageInput {
  const tools: ToolStatus[] = [];
  const chromaticStatus = process.env.CI_OUTAGE_CHROMATIC_STATUS || DEFAULT_STATUS_URLS.chromatic;
  const lighthouseStatus = process.env.CI_OUTAGE_LIGHTHOUSE_STATUS || DEFAULT_STATUS_URLS.lighthouse;

  if (process.env.CI_OUTAGE_CHROMATIC_JOB_STATUS) {
    tools.push({
      name: 'chromatic',
      job: process.env.CI_OUTAGE_CHROMATIC_JOB_NAME || 'visual-accessibility',
      status: process.env.CI_OUTAGE_CHROMATIC_JOB_STATUS,
      statusUrl: chromaticStatus,
      logPath: process.env.CI_OUTAGE_CHROMATIC_LOG,
      failurePatterns: OUTAGE_PATTERNS,
      allowFailOpen: true,
    });
  }
  if (process.env.CI_OUTAGE_LIGHTHOUSE_JOB_STATUS) {
    tools.push({
      name: 'lighthouse',
      job: process.env.CI_OUTAGE_LIGHTHOUSE_JOB_NAME || 'performance',
      status: process.env.CI_OUTAGE_LIGHTHOUSE_JOB_STATUS,
      statusUrl: lighthouseStatus,
      logPath: process.env.CI_OUTAGE_LIGHTHOUSE_LOG,
      failurePatterns: OUTAGE_PATTERNS,
      allowFailOpen: true,
    });
  }
  if (process.env.CI_OUTAGE_AXE_JOB_STATUS) {
    tools.push({
      name: 'axe',
      job: process.env.CI_OUTAGE_AXE_JOB_NAME || 'visual-accessibility',
      status: process.env.CI_OUTAGE_AXE_JOB_STATUS,
      statusUrl: process.env.CI_OUTAGE_AXE_STATUS_URL,
      logPath: process.env.CI_OUTAGE_AXE_LOG,
      failurePatterns: OUTAGE_PATTERNS,
      allowFailOpen: true,
    });
  }

  const refName = process.env.GITHUB_HEAD_REF || process.env.GITHUB_REF_NAME || '';
  const [owner, repository] = (process.env.GITHUB_REPOSITORY || '/').split('/');

  return {
    branch: refName,
    eventName: process.env.GITHUB_EVENT_NAME || 'workflow',
    runId: Number(process.env.GITHUB_RUN_ID || 0),
    runUrl: process.env.GITHUB_SERVER_URL
      ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
      : undefined,
    commit: process.env.GITHUB_SHA || '',
    prNumber: process.env.GITHUB_REF?.startsWith('refs/pull/')
      ? Number(process.env.GITHUB_REF.split('/')[2])
      : process.env.PR_NUMBER
        ? Number(process.env.PR_NUMBER)
        : undefined,
    repository,
    owner,
    githubToken: process.env.GITHUB_TOKEN,
    otelEndpoint: process.env.FOUNDATION_OTEL_OUTAGE_ENDPOINT,
    defaultTenant: process.env.FOUNDATION_DEFAULT_TENANT,
    tools,
  };
}

function isReleaseBranch(branch: string, releaseBranches?: string[]): boolean {
  const patterns = releaseBranches && releaseBranches.length > 0 ? releaseBranches : DEFAULT_RELEASE_BRANCHES;
  return patterns.some((pattern) => {
    if (pattern.endsWith('/')) {
      return branch.startsWith(pattern);
    }
    return branch === pattern;
  });
}

async function evaluateTool(tool: ToolStatus): Promise<ToolEvaluation> {
  const normalizedStatus = normalizeStatus(tool.status);
  if (normalizedStatus === 'success' || normalizedStatus === 'skipped') {
    return {
      tool: tool.name,
      job: tool.job,
      status: normalizedStatus,
      outage: false,
    };
  }

  const statusPage = await checkStatusPage(tool.statusUrl || DEFAULT_STATUS_URLS[tool.name]);
  if (statusPage === 'outage') {
    return {
      tool: tool.name,
      job: tool.job,
      status: normalizedStatus,
      outage: true,
      reason: 'Status page indica indisponibilidade.',
    };
  }
  if (statusPage === 'degraded') {
    return {
      tool: tool.name,
      job: tool.job,
      status: normalizedStatus,
      outage: true,
      reason: 'Status page indica degradação.',
    };
  }

  const logSuggestsOutage = await readLogPatterns(tool.logPath);
  if (logSuggestsOutage) {
    return {
      tool: tool.name,
      job: tool.job,
      status: normalizedStatus,
      outage: true,
      reason: 'Padrões de indisponibilidade detectados nos logs.',
      evidence: tool.logPath,
    };
  }

  return {
    tool: tool.name,
    job: tool.job,
    status: normalizedStatus,
    outage: false,
  };
}

async function annotateGitHub(input: OutageInput, outages: ToolEvaluation[]) {
  if (!input.githubToken || !input.prNumber) {
    return;
  }
  const urlBase = `${process.env.GITHUB_API_URL || 'https://api.github.com'}/repos/${input.owner}/${input.repository}`;
  const headers = {
    Authorization: `Bearer ${input.githubToken}`,
    'Content-Type': 'application/json',
    'User-Agent': 'ci-outage-guard',
  };

  try {
    await fetch(`${urlBase}/issues/${input.prNumber}/labels`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ labels: ['ci-outage'] }),
    });
  } catch (error) {
    console.warn(`[ci-outage] Falha ao aplicar label ci-outage: ${(error as Error).message}`);
  }

  const commentLines = [
    ':warning: **CI Outage Policy ativada**',
    '',
    `Branch: \`${input.branch}\``,
    `Run: ${input.runUrl || `#${input.runId}`}`,
    '',
    'Ferramentas afetadas:',
  ];

  for (const outage of outages) {
    commentLines.push(
      `- ${outage.tool} (${outage.job}) — status ${outage.status} — motivo: ${outage.reason || 'indisponível'}`,
    );
  }

  commentLines.push('');
  commentLines.push(
    'Favor acompanhar a instabilidade e remover o rótulo `ci-outage` assim que os jobs passarem verde novamente.',
  );

  try {
    await fetch(`${urlBase}/issues/${input.prNumber}/comments`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ body: commentLines.join('\n') }),
    });
  } catch (error) {
    console.warn(`[ci-outage] Falha ao registrar comentário: ${(error as Error).message}`);
  }
}

async function emitOtelEvent(input: OutageInput, outages: ToolEvaluation[]) {
  if (!input.otelEndpoint) {
    return;
  }
  const payload = {
    name: 'foundation_ci_outage',
    branch: input.branch,
    runId: input.runId,
    runUrl: input.runUrl,
    commit: input.commit,
    defaultTenant: input.defaultTenant,
    tools: outages.map((outage) => ({
      tool: outage.tool,
      job: outage.job,
      status: outage.status,
      reason: outage.reason,
      evidence: outage.evidence,
    })),
    timestamp: new Date().toISOString(),
  };
  try {
    await fetch(input.otelEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.warn(`[ci-outage] Falha ao enviar evento OTEL: ${(error as Error).message}`);
  }
}

async function writeOutageReport(result: ScriptResult) {
  const outputDir = path.join('observabilidade', 'data');
  await fs.mkdir(outputDir, { recursive: true });
  const filePath = path.join(outputDir, 'ci-outages.json');
  let existing: ScriptResult[] = [];
  try {
    const raw = await fs.readFile(filePath, 'utf-8');
    existing = JSON.parse(raw);
    if (!Array.isArray(existing)) {
      existing = [];
    }
  } catch {
    existing = [];
  }
  existing.push(result);
  await fs.writeFile(filePath, JSON.stringify(existing, null, 2));
}

async function main() {
  const args = parseArgs();
  let input: OutageInput;
  if (args.inputPath) {
    input = await readJson(args.inputPath);
  } else {
    input = buildInputFromEnv();
  }

  const releaseBranches = input.releaseBranches || DEFAULT_RELEASE_BRANCHES;
  const failOpen = !isReleaseBranch(input.branch, releaseBranches);

  const evaluations: ToolEvaluation[] = [];
  for (const tool of input.tools) {
    evaluations.push(await evaluateTool(tool));
  }

  const outages = evaluations.filter((item) => item.outage);
  const result: ScriptResult = {
    generatedAt: new Date().toISOString(),
    branch: input.branch,
    runId: input.runId,
    runUrl: input.runUrl,
    commit: input.commit,
    eventName: input.eventName,
    outages,
    failOpen,
  };

  if (outages.length > 0) {
    await emitOtelEvent(input, outages);
    await writeOutageReport(result);

    if (failOpen) {
      await annotateGitHub(input, outages);
      console.warn(
        `[ci-outage] Política fail-open aplicada em ${input.branch}. Outages detectados: ${outages
          .map((item) => item.tool)
          .join(', ')}`,
      );
    } else {
      console.error(
        `[ci-outage] Branch ${input.branch} está em modo fail-closed. Outages detectados: ${outages
          .map((item) => item.tool)
          .join(', ')}`,
      );
      console.error('[ci-outage] Falhando pipeline conforme política NFR-008.');
      console.error(JSON.stringify(result, null, 2));
      process.exit(1);
    }
  }

  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error('[ci-outage] Erro inesperado', error);
  process.exit(1);
});
