#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');

const summaryPath = path.join(process.cwd(), 'artifacts', 'lighthouse', 'home.summary.json');

if (!fs.existsSync(summaryPath)) {
  console.log('Resumo Lighthouse não encontrado, nada a reportar.');
  process.exit(0);
}

const summary = JSON.parse(fs.readFileSync(summaryPath, 'utf-8'));

const lines = [
  '| Métrica | Valor | Limite | Status |',
  '|---------|-------|--------|--------|',
];

const thresholds = summary.budgets || {};
const metrics = summary.metrics || {};

const checks = [
  ['LCP (ms)', metrics.lcp, thresholds.lcp],
  ['TTI (ms)', metrics.tti, thresholds.tti],
  ['TBT (ms)', metrics.tbt, thresholds.tbt],
  ['CLS', metrics.cls, thresholds.cls],
];

const statusIcon = (value, limit) => {
  if (typeof value !== 'number' || typeof limit !== 'number') {
    return '⚪';
  }
  return value <= limit ? '✅' : '❌';
};

checks.forEach(([label, value, limit]) => {
  if (typeof value === 'number' && typeof limit === 'number') {
    lines.push(`| ${label} | ${value.toFixed(2)} | ${limit} | ${statusIcon(value, limit)} |`);
  } else {
    lines.push(`| ${label} | n/d | n/d | ⚪ |`);
  }
});

const summaryContent = [
  '### Lighthouse Budgets',
  '',
  `URL: ${summary.url}`,
  '',
  ...lines,
  '',
  `Relatório HTML: ${summary.reports?.html}`,
  `Relatório JSON: ${summary.reports?.json}`,
].join('\n');

if (!process.env.GITHUB_STEP_SUMMARY) {
  console.log(summaryContent);
  process.exit(0);
}

fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, summaryContent);

