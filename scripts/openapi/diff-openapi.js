#!/usr/bin/env node
// Minimal OpenAPI diff helper supporting YAML/JSON and OpenAPI 3.1.
// Exits with code 0 when no diff is detected, otherwise prints a summary and exits 1.

const fs = require('fs');
const path = require('path');
const { diffLines } = require('diff');
const YAML = require('yaml');

if (process.argv.length < 4) {
  console.error('Usage: node scripts/openapi/diff-openapi.js <oldSpec> <newSpec>');
  process.exit(2);
}

const [oldPath, newPath] = process.argv.slice(2);

function loadSpec(filePath) {
  const fullPath = path.resolve(filePath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Spec not found: ${fullPath}`);
  }
  const raw = fs.readFileSync(fullPath, 'utf8');
  if (!raw.trim()) {
    throw new Error(`Spec is empty: ${fullPath}`);
  }
  if (filePath.endsWith('.json')) {
    return JSON.parse(raw);
  }
  return YAML.parse(raw);
}

function normalize(spec) {
  // Stable JSON stringify for diff.
  const ordered = JSON.stringify(spec, Object.keys(spec).sort(), 2);
  return ordered + '\n';
}

let oldSpec;
let newSpec;
try {
  oldSpec = loadSpec(oldPath);
  newSpec = loadSpec(newPath);
} catch (err) {
  console.error(`ERROR: ${err.message}`);
  process.exit(2);
}

const oldNorm = normalize(oldSpec);
const newNorm = normalize(newSpec);

if (oldNorm === newNorm) {
  console.log('✓ OpenAPI specs are identical');
  process.exit(0);
}

console.log('⚠ OpenAPI specs differ. Summary:');
const diff = diffLines(oldNorm, newNorm);
for (const part of diff) {
  const prefix = part.added ? '+' : part.removed ? '-' : ' ';
  const lines = part.value.trimEnd().split('\n');
  for (const line of lines) {
    if (!line) continue;
    console.log(`${prefix} ${line}`);
  }
}
process.exit(1);
