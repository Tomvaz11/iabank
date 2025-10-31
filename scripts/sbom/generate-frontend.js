#!/usr/bin/env node
/**
 * Geração de SBOM para o frontend utilizando cyclonedx-npm.
 * O fluxo abaixo utiliza npm apenas para materializar node_modules temporário
 * (necessário para a CLI atual), executa o gerador e limpa os resíduos ao final.
 */

const { execSync } = require('node:child_process');
const { rmSync, existsSync, mkdtempSync, cpSync, writeFileSync, readFileSync, mkdirSync } = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const projectRoot = path.resolve(__dirname, '..', '..');
const frontendDir = path.join(projectRoot, 'frontend');
const outputFile = path.join(frontendDir, 'sbom', 'frontend-foundation.json');

const run = (command, options = {}) => {
  execSync(command, {
    stdio: 'inherit',
    env: {
      ...process.env,
      npm_execpath: process.env.npm_execpath ?? execSync('command -v npm').toString().trim(),
    },
    ...options,
  });
};

const main = () => {
  const tempRoot = mkdtempSync(path.join(os.tmpdir(), 'frontend-sbom-'));
  const tempFrontendDir = path.join(tempRoot, 'frontend');
  const tempScriptsDir = path.join(tempFrontendDir, 'scripts');
  const pluginSource = path.join(frontendDir, 'scripts', 'eslint-plugin-fsd-boundaries');
  const pluginTarget = path.join(tempScriptsDir, 'eslint-plugin-fsd-boundaries');

  try {
    mkdirSync(tempScriptsDir, { recursive: true });
    cpSync(path.join(frontendDir, 'package.json'), path.join(tempFrontendDir, 'package.json'));
    cpSync(pluginSource, pluginTarget, { recursive: true });

    // Garante que dependência local esteja apontando para pasta relativa correta.
    const packageJsonPath = path.join(tempFrontendDir, 'package.json');
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    if (
      packageJson.devDependencies &&
      packageJson.devDependencies['eslint-plugin-fsd-boundaries']
    ) {
      packageJson.devDependencies['eslint-plugin-fsd-boundaries'] = './scripts/eslint-plugin-fsd-boundaries';
      writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
    }

    run('npm install --ignore-scripts --legacy-peer-deps', { cwd: tempFrontendDir });
    run(
      `npx @cyclonedx/cyclonedx-npm --ignore-npm-errors --output-format json --output-file ${outputFile}`,
      { cwd: tempFrontendDir },
    );
  } finally {
    if (existsSync(tempRoot)) {
      rmSync(tempRoot, { recursive: true, force: true });
    }
  }
};

main();
