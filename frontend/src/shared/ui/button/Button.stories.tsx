import type { Meta, StoryObj } from '@storybook/react';
import { expect, within } from '@storybook/test';

type TenantKey = 'tenant-default' | 'tenant-alfa' | 'tenant-beta';

type ButtonStoryProps = {
  label: string;
  tenant: TenantKey;
};

const THEMES: Record<TenantKey, { background: string; foreground: string }> = {
  'tenant-default': {
    background: 'rgb(30, 58, 138)',
    foreground: 'rgb(248, 250, 252)',
  },
  'tenant-alfa': {
    background: 'rgb(15, 118, 110)',
    foreground: 'rgb(240, 253, 250)',
  },
  'tenant-beta': {
    background: 'rgb(124, 58, 237)',
    foreground: 'rgb(245, 243, 255)',
  },
};

const meta: Meta<ButtonStoryProps> = {
  title: 'Shared/UI/Button',
  parameters: {
    layout: 'centered',
    chromatic: { disableSnapshot: false },
  },
  args: {
    label: 'Continuar',
  },
  render: ({ label }) => (
    <button type="button" className="shared-button" data-variant="primary">
      {label}
    </button>
  ),
};

export default meta;

type Story = StoryObj<ButtonStoryProps>;

const playStoryForTenant =
  (tenant: TenantKey): Story['play'] =>
  async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const button = await canvas.findByRole('button', { name: args.label });

    expect(document.documentElement.dataset.tenant).toBe(tenant);

    const computed = window.getComputedStyle(button);
    const expectedTheme = THEMES[tenant];

    expect(computed.backgroundColor).toBe(expectedTheme.background);
    expect(computed.color).toBe(expectedTheme.foreground);
  };

export const TenantDefault: Story = {
  name: 'Tenant default',
  args: { tenant: 'tenant-default' },
  parameters: { tenant: 'tenant-default' },
  play: playStoryForTenant('tenant-default'),
};

export const TenantAlfa: Story = {
  name: 'Tenant Alfa',
  args: { tenant: 'tenant-alfa', label: 'Continuar (Alfa)' },
  parameters: { tenant: 'tenant-alfa' },
  play: playStoryForTenant('tenant-alfa'),
};

export const TenantBeta: Story = {
  name: 'Tenant Beta',
  args: { tenant: 'tenant-beta', label: 'Continuar (Beta)' },
  parameters: { tenant: 'tenant-beta' },
  play: playStoryForTenant('tenant-beta'),
};
