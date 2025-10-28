import { readFile } from 'node:fs/promises';
import path from 'node:path';
import ts from 'typescript';

const TS_EXTENSIONS = new Set(['.ts', '.tsx']);
const RELATIVE_IMPORT_PATTERN = /^\.{1,2}\//;

const tryResolveWithExtension = async (specifier, context, defaultResolve) => {
  let lastError;

  for (const extension of TS_EXTENSIONS) {
    try {
      const resolution = await defaultResolve(`${specifier}${extension}`, context, defaultResolve);
      return {
        ...resolution,
        format: 'module',
      };
    } catch (error) {
      if (error?.code !== 'ERR_MODULE_NOT_FOUND') {
        throw error;
      }
      lastError = error;
    }
  }

  if (lastError) {
    throw lastError;
  }

  return defaultResolve(specifier, context, defaultResolve);
};

export async function resolve(specifier, context, defaultResolve) {
  if (TS_EXTENSIONS.has(path.extname(specifier))) {
    const resolved = await defaultResolve(specifier, context, defaultResolve);
    return {
      ...resolved,
      format: 'module',
    };
  }

  if (!path.extname(specifier) && RELATIVE_IMPORT_PATTERN.test(specifier)) {
    return tryResolveWithExtension(specifier, context, defaultResolve);
  }

  return defaultResolve(specifier, context, defaultResolve);
}

export async function load(url, context, defaultLoad) {
  if (TS_EXTENSIONS.has(path.extname(new URL(url).pathname))) {
    const source = await readFile(new URL(url), 'utf-8');
    const output = ts.transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2021,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
        moduleResolution: ts.ModuleResolutionKind.NodeNext,
        importHelpers: false,
      },
      fileName: url,
    });

    return {
      format: 'module',
      shortCircuit: true,
      source: output.outputText,
    };
  }

  return defaultLoad(url, context, defaultLoad);
}
