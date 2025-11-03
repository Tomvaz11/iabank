#!/usr/bin/env node
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { setTimeout: delay } = require('node:timers/promises');
const net = require('node:net');

const FRONTEND_SCOPE = '@iabank/frontend-foundation';
const PREVIEW_DEFAULT_HOST = process.env.FOUNDATION_PERF_HOST ?? '127.0.0.1';
const PREVIEW_REQUESTED_PORT = Number(process.env.FOUNDATION_PERF_PORT ?? '4173');

const withLogging = (message) => {
  // eslint-disable-next-line no-console
  console.log(`[perf:smoke] ${message}`);
};

const runCommand = (command, args, options = {}) =>
  new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: 'inherit',
      shell: false,
      ...options,
    });

    child.on('error', reject);
    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(' ')} finalizou com código ${code}`));
      }
    });
  });

const waitForPreview = async (url, timeoutMs = 60000) => {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { method: 'GET' });
      if (response.ok || response.status < 500) {
        return;
      }
    } catch {
      // Server ainda iniciando — aguardar.
    }

    await delay(1000);
  }

  throw new Error(`Servidor Vite não respondeu em ${timeoutMs / 1000}s (${url}).`);
};

const ensurePortAvailable = (port, host) =>
  new Promise((resolve, reject) => {
    const server = net.createServer();

    server.once('error', (error) => {
      server.close();
      reject(error);
    });

    server.once('listening', () => {
      server.close(() => resolve(true));
    });

    server.listen(port, host);
  });

const findAvailablePort = async (port, host, maxAttempts = 5) => {
  let currentPort = port;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      await ensurePortAvailable(currentPort, host);
      return currentPort;
    } catch (error) {
      if (error && error.code === 'EADDRINUSE') {
        withLogging(`Porta ${currentPort} ocupada — tentando ${currentPort + 1}`);
        currentPort += 1;
        continue;
      }
      throw error;
    }
  }

  throw new Error(
    `Nenhuma porta disponível entre ${port} e ${port + maxAttempts - 1}. Ajuste FOUNDATION_PERF_PORT.`,
  );
};

const normalizeK6Args = (rawArgs) => {
  if (!Array.isArray(rawArgs)) {
    return [];
  }

  if (rawArgs.length > 0 && rawArgs[0] === '--') {
    return rawArgs.slice(1);
  }

  return rawArgs;
};

const main = async () => {
  const skipBuild = process.env.FOUNDATION_PERF_SKIP_BUILD === 'true';
  const extraArgs = normalizeK6Args(process.argv.slice(2));

  const previewPort = await findAvailablePort(PREVIEW_REQUESTED_PORT, PREVIEW_DEFAULT_HOST);
  const previewBaseUrl =
    process.env.FOUNDATION_PERF_BASE_URL ?? `http://${PREVIEW_DEFAULT_HOST}:${previewPort}`;

  if (!skipBuild) {
    withLogging('Executando build do frontend antes do preview');
    await runCommand('pnpm', ['--filter', FRONTEND_SCOPE, 'build']);
  } else {
    withLogging('Variável FOUNDATION_PERF_SKIP_BUILD= true — etapa de build ignorada');
  }

  // Importante: usar `pnpm exec vite preview` ao invés de `pnpm run preview -- ...`
  // pois alguns ambientes estavam propagando um argumento literal "--" para o Vite,
  // fazendo com que as flags subsequentes fossem ignoradas (e o Vite tentasse a porta 4173).
  const previewArgs = [
    '--filter',
    FRONTEND_SCOPE,
    'exec',
    'vite',
    'preview',
    '--host',
    PREVIEW_DEFAULT_HOST,
    '--port',
    String(previewPort),
    '--strictPort',
  ];

  withLogging(`Iniciando Vite preview em ${previewBaseUrl} (porta ${previewPort})`);

  const previewEnv = {
    ...process.env,
    FOUNDATION_PERF_PORT: String(previewPort),
    FOUNDATION_PERF_BASE_URL: previewBaseUrl,
  };

  const previewProcess = spawn('pnpm', previewArgs, {
    stdio: 'inherit',
    shell: false,
    env: previewEnv,
  });

  let previewReady = false;

  const teardownPreview = async () => {
    if (previewProcess.killed || previewProcess.exitCode != null) {
      return;
    }
    previewProcess.kill('SIGINT');
    const timeout = delay(3000).then(() => {
      if (previewProcess.exitCode == null && !previewProcess.killed) {
        previewProcess.kill('SIGTERM');
      }
    });
    await Promise.race([once(previewProcess, 'exit'), timeout]);
    if (previewProcess.exitCode == null && !previewProcess.killed) {
      previewProcess.kill('SIGKILL');
      await once(previewProcess, 'exit');
    }
  };

  const handleSignal = async (signal) => {
    withLogging(`Sinal ${signal} recebido — finalizando processos filhos`);
    await teardownPreview();
    process.exit(1);
  };

  process.once('SIGINT', handleSignal);
  process.once('SIGTERM', handleSignal);

  previewProcess.on('exit', (code) => {
    if (!previewReady && code !== 0) {
      withLogging('Vite preview saiu antes de ficar pronto.');
    }
  });

  try {
    await waitForPreview(`${previewBaseUrl}/`, 60000);
    previewReady = true;
    withLogging('Preview disponível — iniciando k6');

    await runCommand('pnpm', ['k6', 'run', ...extraArgs, 'tests/performance/frontend-smoke.js'], {
      env: {
        ...previewEnv,
      },
    });
  } finally {
    await teardownPreview();
    process.removeListener('SIGINT', handleSignal);
    process.removeListener('SIGTERM', handleSignal);
  }
};

main().catch((error) => {
  // eslint-disable-next-line no-console
  console.error('[perf:smoke] Falha ao executar teste de performance:', error);
  process.exitCode = 1;
});
