import { describe, test } from 'vitest';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import path from 'node:path';
import { RuleTester } from 'eslint';

// eslint-plugin-fsd-boundaries é CommonJS; usar require para compatibilidade.
// eslint-disable-next-line @typescript-eslint/no-var-requires, @typescript-eslint/no-require-imports -- CommonJS interop necessário
const plugin = require('../../scripts/eslint-plugin-fsd-boundaries');
const requireModule = createRequire(import.meta.url);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_SRC = path.resolve(__dirname, '../../src');

RuleTester.setDefaultConfig({
  parser: requireModule.resolve('@typescript-eslint/parser'),
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module'
  }
});

RuleTester.it = test;
RuleTester.describe = describe;

const ruleTester = new RuleTester();

const featureFile = (feature: string, file = 'index.ts') =>
  path.join(FRONTEND_SRC, 'features', feature, file);

const entityFile = (entity: string, file = 'index.ts') =>
  path.join(FRONTEND_SRC, 'entities', entity, file);

ruleTester.run('enforce-layer-boundaries', plugin.rules['enforce-layer-boundaries'], {
  valid: [
    {
      filename: featureFile('accounts', 'model.ts'),
      code: "import { getUser } from '@entities/user';"
    },
    {
      filename: featureFile('accounts', 'ui/Button.tsx'),
      code: "import type { ButtonProps } from './types';"
    },
    {
      filename: entityFile('user', 'model.ts'),
      code: "import { httpClient } from '@shared/api';"
    }
  ],
  invalid: [
    {
      filename: featureFile('accounts', 'ui/view.tsx'),
      code: "import { usePayments } from '@features/payments';",
      errors: [
        {
          messageId: 'crossFeatureImport'
        }
      ]
    },
    {
      filename: featureFile('accounts', 'model/service.ts'),
      code: "import { query } from '@entities/user/model/internal';",
      errors: [
        {
          messageId: 'privateImport',
          data: {
            layer: 'entities',
            slice: 'user'
          }
        }
      ]
    }
  ]
});
