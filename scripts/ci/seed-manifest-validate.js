#!/usr/bin/env node

// Valida manifestos seed_profile contra os caps Q11 e regras básicas do schema v1.
const fs = require('fs');
const path = require('path');
const YAML = require('yaml');

const args = process.argv.slice(2);
const flags = {};
for (let i = 0; i < args.length; i += 1) {
  const key = args[i];
  if (key === '--schema' || key === '--root') {
    flags[key.replace(/^--/, '')] = args[i + 1];
    i += 1;
  }
}

const rootDir = flags.root ? path.resolve(flags.root) : process.cwd();
const manifestsDir = path.join(rootDir, 'configs', 'seed_profiles');
const schemaPath =
  flags.schema || path.join(rootDir, 'contracts', 'seed-profile.schema.json');

const allowedEnvs = ['dev', 'homolog', 'staging', 'perf', 'dr'];
const envMultipliers = { dev: 1, homolog: 3, staging: 5, perf: 5, dr: 5 };
const allowedModes = ['baseline', 'carga', 'dr', 'canary'];

const capsByMode = {
  baseline: {
    tenant_users: 5,
    customers: 100,
    addresses: 150,
    consultants: 10,
    bank_accounts: 120,
    account_categories: 20,
    suppliers: 30,
    loans: 200,
    installments: 2000,
    financial_transactions: 4000,
    limits: 100,
    contracts: 150,
  },
  carga: {
    tenant_users: 10,
    customers: 500,
    addresses: 750,
    consultants: 30,
    bank_accounts: 600,
    account_categories: 60,
    suppliers: 150,
    loans: 1000,
    installments: 10000,
    financial_transactions: 20000,
    limits: 500,
    contracts: 750,
  },
  dr: {
    tenant_users: 10,
    customers: 500,
    addresses: 750,
    consultants: 30,
    bank_accounts: 600,
    account_categories: 60,
    suppliers: 150,
    loans: 1000,
    installments: 10000,
    financial_transactions: 20000,
    limits: 500,
    contracts: 750,
  },
};

const rateLimitByEnv = { dev: 240, homolog: 480, staging: 960, perf: 960, dr: 960 };
const budgetCapByEnv = { dev: 25, homolog: 25, staging: 125, perf: 125, dr: 125 };
const piiPatterns = [
  { name: 'cpf', regex: /\b\d{3}\.\d{3}\.\d{3}-\d{2}\b/ },
  { name: 'email', regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i },
  { name: 'telefone', regex: /\+?\d{2,3}\s?\(?\d{2}\)?\s?\d{4,5}-\d{4}/ },
];

function readJson(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (err) {
    throw new Error(`Falha ao ler JSON ${p}: ${err.message}`);
  }
}

function readYaml(p) {
  try {
    const raw = fs.readFileSync(p, 'utf8');
    return YAML.parse(raw);
  } catch (err) {
    throw new Error(`Falha ao ler YAML ${p}: ${err.message}`);
  }
}

function listManifests(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return listManifests(entryPath);
    }
    if (entry.isFile() && entry.name.endsWith('.yaml')) {
      return [entryPath];
    }
    return [];
  });
}

function ensure(cond, message, context) {
  if (!cond) {
    const prefix = context ? `${context}: ` : '';
    throw new Error(`${prefix}${message}`);
  }
}

function validateVolumetry(manifest, expectedCaps, multiplier, context) {
  const volumetry = manifest.volumetry || {};
  const expectedKeys = Object.keys(expectedCaps);
  const keys = Object.keys(volumetry);
  ensure(
    keys.length === expectedKeys.length &&
      expectedKeys.every((k) => keys.includes(k)),
    'volumetry deve conter exatamente o catálogo de entidades esperado',
    context,
  );

  for (const entity of expectedKeys) {
    const caps = volumetry[entity] || {};
    ensure(Number.isInteger(caps.cap), `cap da entidade ${entity} deve ser inteiro`, context);
    const expectedCap = expectedCaps[entity] * multiplier;
    ensure(
      caps.cap === expectedCap,
      `cap de ${entity} divergente (esperado=${expectedCap}, encontrado=${caps.cap})`,
      context,
    );
    if (caps.target_pct !== undefined) {
      ensure(
        typeof caps.target_pct === 'number' &&
          caps.target_pct >= 0 &&
          caps.target_pct <= 100,
        `target_pct inválido em ${entity}`,
        context,
      );
    }
  }
}

function validateRateLimit(manifest, env, context) {
  const rate = manifest.rate_limit || {};
  const expectedLimit = rateLimitByEnv[env];
  ensure(Number.isInteger(rate.limit), 'rate_limit.limit deve ser inteiro', context);
  ensure(
    rate.limit === expectedLimit,
    `rate_limit.limit divergente (esperado=${expectedLimit}, encontrado=${rate.limit})`,
    context,
  );
  ensure(
    Number.isInteger(rate.window_seconds) && rate.window_seconds > 0,
    'rate_limit.window_seconds deve ser inteiro positivo',
    context,
  );
  if (rate.burst !== undefined) {
    ensure(rate.burst >= rate.limit, 'rate_limit.burst deve ser >= limit', context);
  }
}

function validateBudget(manifest, env, context) {
  const budget = manifest.budget || {};
  const expectedCap = budgetCapByEnv[env];
  ensure(typeof budget.cost_cap_brl === 'number', 'budget.cost_cap_brl deve ser numérico', context);
  ensure(
    budget.cost_cap_brl <= expectedCap,
    `budget.cost_cap_brl acima do teto (${expectedCap})`,
    context,
  );
  ensure(
    typeof budget.error_budget_pct === 'number' &&
      budget.error_budget_pct >= 0 &&
      budget.error_budget_pct <= 100,
    'budget.error_budget_pct deve estar entre 0 e 100',
    context,
  );
}

function validateIntegrity(manifest, context) {
  const hash = manifest.integrity && manifest.integrity.manifest_hash;
  ensure(typeof hash === 'string', 'integrity.manifest_hash ausente', context);
  ensure(/^[a-f0-9]{64}$/.test(hash), 'integrity.manifest_hash deve ser hex de 64 chars', context);
}

function validateSlo(manifest, context) {
  const slo = manifest.slo || {};
  ensure(Number.isInteger(slo.p95_target_ms) && slo.p95_target_ms > 0, 'slo.p95_target_ms inválido', context);
  ensure(Number.isInteger(slo.p99_target_ms) && slo.p99_target_ms > 0, 'slo.p99_target_ms inválido', context);
  ensure(
    typeof slo.throughput_target_rps === 'number' && slo.throughput_target_rps > 0,
    'slo.throughput_target_rps deve ser numérico positivo',
    context,
  );
}

function validateTtl(manifest, context) {
  const ttl = manifest.ttl || {};
  ['baseline_days', 'carga_days', 'dr_days'].forEach((field) => {
    ensure(
      Number.isInteger(ttl[field]) && ttl[field] >= 0,
      `ttl.${field} deve ser inteiro >= 0`,
      context,
    );
  });
}

function collectPiiStrings(value, pathSoFar = '') {
  const findings = [];
  if (typeof value === 'string') {
    for (const pattern of piiPatterns) {
      if (pattern.regex.test(value)) {
        findings.push({ path: pathSoFar || '<root>', type: pattern.name, sample: value });
        break;
      }
    }
    return findings;
  }

  if (Array.isArray(value)) {
    value.forEach((item, idx) => {
      findings.push(...collectPiiStrings(item, `${pathSoFar}[${idx}]`));
    });
    return findings;
  }

  if (value && typeof value === 'object') {
    Object.entries(value).forEach(([key, child]) => {
      const childPath = pathSoFar ? `${pathSoFar}.${key}` : key;
      findings.push(...collectPiiStrings(child, childPath));
    });
  }
  return findings;
}

function main() {
  if (!fs.existsSync(schemaPath)) {
    throw new Error(`Schema não encontrado em ${schemaPath}`);
  }
  if (!fs.existsSync(manifestsDir)) {
    throw new Error(`Diretório de manifestos não encontrado: ${manifestsDir}`);
  }
  // Valida apenas se o JSON é parseável (sem usar validador completo neste passo).
  readJson(schemaPath);

  const manifests = listManifests(manifestsDir);
  if (manifests.length === 0) {
    throw new Error(`Nenhum manifesto encontrado em ${manifestsDir}`);
  }

  for (const manifestPath of manifests) {
    const manifest = readYaml(manifestPath);
    const context = manifestPath;
    ensure(manifest.metadata, 'metadata ausente', context);
    const { environment, schema_version: schemaVersion, tenant } = manifest.metadata;
    ensure(tenant, 'metadata.tenant ausente', context);
    ensure(schemaVersion === 'v1', 'metadata.schema_version deve ser v1', context);
    ensure(
      allowedEnvs.includes(environment),
      `environment inválido (esperado: ${allowedEnvs.join(', ')})`,
      context,
    );
    ensure(allowedModes.includes(manifest.mode), 'mode inválido', context);
    if (['dev', 'homolog'].includes(environment) && manifest.mode !== 'baseline') {
      throw new Error(`${context}: modo ${manifest.mode} não permitido para ${environment} (apenas baseline)`);
    }
    const multiplier = envMultipliers[environment];
    const expectedCaps = capsByMode[manifest.mode];
    ensure(multiplier, 'multiplicador por ambiente não configurado', context);
    ensure(expectedCaps, 'caps não definidos para o modo informado', context);

    validateVolumetry(manifest, expectedCaps, multiplier, context);
    validateRateLimit(manifest, environment, context);
    validateBudget(manifest, environment, context);
    validateIntegrity(manifest, context);
    validateSlo(manifest, context);
    validateTtl(manifest, context);

    const { window } = manifest;
    ensure(window && typeof window.start_utc === 'string', 'window.start_utc ausente', context);
    ensure(window && typeof window.end_utc === 'string', 'window.end_utc ausente', context);

    const piiFindings = collectPiiStrings(manifest);
    ensure(
      piiFindings.length === 0,
      `PII detectado no manifesto: ${piiFindings
        .slice(0, 5)
        .map((f) => `${f.type}@${f.path}`)
        .join(', ')}${piiFindings.length > 5 ? ' ...' : ''}`,
      context,
    );
  }

  console.log(`Validação concluída: ${manifests.length} manifestos verificados.`);
}

try {
  main();
} catch (err) {
  console.error(`[seed-manifest-validate] ${err.message}`);
  process.exit(1);
}
