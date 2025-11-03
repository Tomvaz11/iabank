import type { StorybookConfig } from '@storybook/react-vite';
import type { InlineConfig } from 'vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
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
