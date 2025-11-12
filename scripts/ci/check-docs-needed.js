#!/usr/bin/env node
/*
 Verificação geral de documentação:
 - Falha o PR se houver mudanças em áreas sensíveis (versões/infra/CI/contracts)
   sem alterações em arquivos de documentação (README/CONTRIBUTING/docs/**).
 - Verifica drift básico de versões (Node major a partir de .nvmrc e Poetry pin do workflow)
   contra o README.

 Execução local (opcional):
   node scripts/ci/check-docs-needed.js

 No GitHub Actions, o script usa GITHUB_EVENT_PATH para detectar base SHA do PR/push.
*/

const fs = require('fs');
const path = require('path');
const cp = require('child_process');

function readJSON(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch {
    return null;
  }
}

function readText(p) {
  try {
    return fs.readFileSync(p, 'utf8');
  } catch {
    return '';
  }
}

function git(args, opts = {}) {
  return require('child_process').execSync(`git ${args}`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], ...opts }).trim();
}

function unique(arr) {
  return Array.from(new Set(arr));
}

function getBaseSha() {
  const eventPath = process.env.GITHUB_EVENT_PATH;
  if (eventPath && fs.existsSync(eventPath)) {
    const event = readJSON(eventPath) || {};
    if (event.pull_request && event.pull_request.base && event.pull_request.base.sha) {
      return event.pull_request.base.sha;
    }
    if (event.before) return event.before;
  }
  // Fallbacks locais
  try {
    // Tenta merge-base com origin/main (se disponível)
    return git('merge-base origin/main HEAD');
  } catch {
    try {
      // Último commit
      return git('rev-parse HEAD~1');
    } catch {
      // Repositório com 1 commit
      return git('rev-parse HEAD');
    }
  }
}

function listChangedFiles(baseSha) {
  try {
    const out = git(`diff --name-only ${baseSha}..HEAD`);
    return out.split('\n').filter(Boolean);
  } catch {
    try {
      const out = git('diff --name-only HEAD~1..HEAD');
      return out.split('\n').filter(Boolean);
    } catch {
      return [];
    }
  }
}

function matchAnyPrefix(file, prefixes) {
  return prefixes.some((p) => file === p || file.startsWith(p.endsWith('/') ? p : p + '/'));
}

function main() {
  const repoRoot = process.cwd();
  const baseSha = getBaseSha();
  const changed = listChangedFiles(baseSha);

  // Áreas cujo ajuste costuma demandar atualização de docs
  const impactPrefixes = [
    '.nvmrc',
    'package.json',
    'pnpm-lock.yaml',
    'pyproject.toml',
    'poetry.lock',
    '.github/workflows/',
    'infra/',
    'contracts/api.yaml',
  ];

  // Locais considerados documentação
  const docsPrefixes = [
    'README.md',
    'CONTRIBUTING.md',
    'docs/',
    'specs/',
    'observabilidade/',
  ];

  const impactChanged = unique(changed.filter((f) => matchAnyPrefix(f, impactPrefixes)));
  const docsChanged = unique(changed.filter((f) => matchAnyPrefix(f, docsPrefixes)));

  let hadError = false;
  const eventName = process.env.GITHUB_EVENT_NAME || '';

  if (impactChanged.length > 0 && docsChanged.length === 0) {
    const msgHead = 'Mudanças impactantes sem atualização de documentação detectada.';
    const log = (level) => (text) => console.error(`::${level}::${text}`);
    const emit = eventName === 'pull_request' ? log('error') : log('warning');
    emit(msgHead);
    console.error('Arquivos impactantes alterados:');
    for (const f of impactChanged) console.error(`- ${f}`);
    console.error('Sugestão: atualize README.md/CONTRIBUTING.md ou docs/ conforme aplicável.');
    if (eventName === 'pull_request') hadError = true;
  }

  // Drift básico de versões
  // Node major de .nvmrc vs README (busca "Node.js <major>")
  const nvmrc = readText(path.join(repoRoot, '.nvmrc')).trim();
  const nodeMajor = /^([0-9]+)/.exec(nvmrc)?.[1];
  const readme = readText(path.join(repoRoot, 'README.md'));
  if (nodeMajor && !new RegExp(`Node\\.js\\s+${nodeMajor}(?![0-9])`).test(readme)) {
    const emit = eventName === 'pull_request' ? 'error' : 'warning';
    console.error(`::${emit}::README não menciona Node.js ${nodeMajor} (extraído de .nvmrc=${nvmrc}).`);
    if (eventName === 'pull_request') hadError = true;
  }

  // Poetry versão pinada no workflow vs README
  const wf = readText(path.join(repoRoot, '.github/workflows/frontend-foundation.yml'));
  const poetryPin = /poetry==([0-9]+\.[0-9]+\.[0-9]+)/.exec(wf)?.[1];
  if (poetryPin && !readme.includes(`poetry==${poetryPin}`) && !readme.includes(`Poetry ${poetryPin}`)) {
    const emit = eventName === 'pull_request' ? 'error' : 'warning';
    console.error(`::${emit}::README não reflete Poetry ${poetryPin} (pin no workflow).`);
    if (eventName === 'pull_request') hadError = true;
  }

  // Python versão principal de pyproject vs README
  const pyproject = readText(path.join(repoRoot, 'pyproject.toml'));
  const pyReq = /python\s*=\s*"\^([0-9]+\.[0-9]+)"/.exec(pyproject)?.[1];
  if (pyReq && !new RegExp(`Python\\s+${pyReq}(?![0-9])`).test(readme)) {
    const emit = eventName === 'pull_request' ? 'error' : 'warning';
    console.error(`::${emit}::README não menciona Python ${pyReq} (de pyproject.toml).`);
    if (eventName === 'pull_request') hadError = true;
  }

  if (hadError) {
    process.exit(1);
  } else {
    console.log('::notice::Verificação de documentação OK.');
  }
}

main();
