import type { StorybookConfig } from '@storybook/react-vite';
import type { InlineConfig } from 'vite';

// Permite desabilitar o addon de a11y quando o test-runner executa checagens via axe-playwright
// para evitar corrida "Axe is already running".
const addons: StorybookConfig['addons'] = [
  '@storybook/addon-essentials',
  '@storybook/addon-interactions',
];

if (process.env.STORYBOOK_DISABLE_A11Y !== 'true') {
  addons.push('@storybook/addon-a11y');
}

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(ts|tsx)'],
  addons,
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
  // Ajuste para reduzir ruído de warnings de chunk size durante build do Storybook
  viteFinal: async (baseConfig: InlineConfig) => {
    return {
      ...baseConfig,
      build: {
        ...(baseConfig.build ?? {}),
        chunkSizeWarningLimit: Math.max(1500, baseConfig.build?.chunkSizeWarningLimit ?? 1500),
      },
    } as InlineConfig;
  },
};

export default config;
