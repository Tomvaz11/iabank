module.exports = {
  root: true,
  env: {
    browser: true,
    es2023: true,
    node: true
  },
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true
    }
  },
  settings: {
    react: {
      version: 'detect'
    }
  },
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'testing-library',
    'jest-dom',
    'fsd-boundaries'
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:testing-library/react',
    'plugin:jest-dom/recommended',
    'prettier'
  ],
  ignorePatterns: ['dist', 'build', 'coverage'],
  rules: {
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-unused-vars': [
      'warn',
      {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_'
      }
    ],
    'fsd-boundaries/enforce-layer-boundaries': 'error',
    'fsd-boundaries/no-zustand-outside-store': 'error'
  },
  overrides: [
    {
      files: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}', 'tests/**/*.{ts,tsx}'],
      rules: {
        'fsd-boundaries/enforce-layer-boundaries': 'off',
        'fsd-boundaries/no-zustand-outside-store': 'off'
      }
    },
    {
      files: ['tests/e2e/**/*.{ts,tsx}'],
      rules: {
        'testing-library/prefer-screen-queries': 'off',
        'testing-library/render-result-naming-convention': 'off'
      }
    },
    {
      files: ['vite.config.ts', 'vitest.config.ts', 'playwright.config.ts'],
      env: {
        browser: false,
        node: true
      }
    }
  ]
};
