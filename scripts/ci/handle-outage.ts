/* eslint-disable @typescript-eslint/no-explicit-any */
// CI: validação prática da issue #86 (canário) — alteração sem efeito funcional
export {};

const fs = require('node:fs/promises');
const path = require('node:path');

const timers = require('timers/promises');
async function sleep(ms: number) {
  await timers.setTimeout(ms);
}

async function fetchWithRetry(
  url: string,
  init?: any,
  attempts = 3,
  backoffMs = 300,
): Promise<any> {
  let lastError: unknown;
  for (let i = 0; i < attempts; i += 1) {
    try {
      const res = await fetch(url, init);
      if (!res.ok && res.status !== 429 && res.status < 500) {
        return res;
      }
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      return res;
    } catch (err) {
      lastError = err;
      if (i < attempts - 1) {
        await sleep(backoffMs);
        backoffMs *= 2;
        continue;
      }
    }
  }
  throw lastError instanceof Error ? lastError : new Error('fetchWithRetry failed');
}

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
    const response = await fetchWithRetry(url, { method: 'GET' }, 3, 300);
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
    await fetchWithRetry(
      `${urlBase}/issues/${input.prNumber}/labels`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ labels: ['ci-outage'] }),
      },
      3,
      300,
    );
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
    await fetchWithRetry(
      `${urlBase}/issues/${input.prNumber}/comments`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ body: commentLines.join('\n') }),
      },
      3,
      300,
    );
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
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    // Opcional: autenticação simples via cabeçalho X-Token
    const token = process.env.FOUNDATION_OTEL_OUTAGE_TOKEN;
    if (token && token.length > 0) {
      headers['X-Token'] = token;
    }
    const resp = await fetchWithRetry(
      input.otelEndpoint,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      },
      3,
      300,
    );
    if (!resp.ok) {
      const text = await resp.text().catch(() => '');
      console.warn(
        `[ci-outage] OTEL endpoint respondeu ${resp.status} ${resp.statusText}. Corpo: ${text?.slice(0, 200)}`,
      );
    }
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
    // Quando um arquivo de input é fornecido, faça merge com as variáveis de ambiente
    // para preencher campos ausentes (ex.: otelEndpoint, githubToken, owner/repository).
    const fileInput: OutageInput = await readJson(args.inputPath);
    const envInput: OutageInput = buildInputFromEnv();
    // Mesclar ferramentas por "name" preservando logPath/statusUrl do ENV
    const mergeTools = (envTools: ToolStatus[], fileTools?: ToolStatus[]): ToolStatus[] => {
      if (!fileTools || fileTools.length === 0) return envTools;
      const byName = new Map<string, ToolStatus>();
      for (const t of envTools) {
        byName.set(t.name, { ...t });
      }
      const result: ToolStatus[] = [];
      for (const ft of fileTools) {
        const base = byName.get(ft.name);
        if (base) {
          // status do arquivo prevalece; preencha ausentes com ENV
          result.push({
            name: ft.name,
            job: ft.job || base.job,
            status: ft.status || base.status,
            statusUrl: ft.statusUrl || base.statusUrl,
            logPath: ft.logPath || base.logPath,
            failurePatterns: ft.failurePatterns || base.failurePatterns,
            allowFailOpen: typeof ft.allowFailOpen === 'boolean' ? ft.allowFailOpen : base.allowFailOpen,
          });
          byName.delete(ft.name);
        } else {
          // Sem base: mantenha tool do arquivo e deixe defaults para avaliação (statusUrl por nome)
          result.push({
            name: ft.name,
            job: ft.job || 'unknown',
            status: ft.status || 'unknown',
            statusUrl: ft.statusUrl, // evaluateTool usará DEFAULT_STATUS_URLS se faltar
            logPath: ft.logPath,
            failurePatterns: ft.failurePatterns || OUTAGE_PATTERNS,
            allowFailOpen: typeof ft.allowFailOpen === 'boolean' ? ft.allowFailOpen : true,
          });
        }
      }
      // Itens do ENV que não apareceram no arquivo (mantém)
      for (const rest of byName.values()) {
        result.push(rest);
      }
      return result;
    };
    input = {
      ...envInput,
      ...fileInput,
      // Mescla por nome: preserva logPath/statusUrl do ENV e status vindo do arquivo
      tools: mergeTools(envInput.tools, fileInput.tools),
      // Se releaseBranches não vier do arquivo, preserve as do ambiente
      releaseBranches:
        Array.isArray(fileInput.releaseBranches) && fileInput.releaseBranches.length > 0
          ? fileInput.releaseBranches
          : envInput.releaseBranches,
    };
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
