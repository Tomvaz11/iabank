// Ajuste mínimo para validar gating de UI no CI (nudge commit)
import type { Meta, StoryObj } from '@storybook/react';
import { expect, within } from '@storybook/test';

import { Button, BUTTON_SIZES, BUTTON_VARIANTS } from './Button';
import type { ButtonProps } from './Button';

type TenantKey = 'tenant-default' | 'tenant-alfa' | 'tenant-beta';

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

const meta: Meta<ButtonProps & { tenant: TenantKey }> = {
  title: 'Shared/UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    chromatic: { disableSnapshot: false },
  },
  args: {
    children: 'Continuar',
    variant: 'primary',
    size: 'md',
  },
  render: ({ tenant: _tenant, ...props }) => <Button {...props} />,
  argTypes: {
    variant: {
      control: 'inline-radio',
      options: BUTTON_VARIANTS,
    },
    size: {
      control: 'inline-radio',
      options: BUTTON_SIZES,
    },
    tenant: {
      control: false,
    },
  },
};

export default meta;

type Story = StoryObj<ButtonProps & { tenant: TenantKey }>;

const playStoryForTenant =
  (tenant: TenantKey): Story['play'] =>
  async ({ canvasElement, args }) => {
    const canvas = within(canvasElement);
    const button = await canvas.findByRole('button', { name: args.children as string });

    expect(document.documentElement.dataset.tenant).toBe(tenant);
    expect(button.dataset.variant).toBe(args.variant ?? 'primary');

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
  args: { tenant: 'tenant-alfa', children: 'Continuar (Alfa)' },
  parameters: { tenant: 'tenant-alfa' },
  play: playStoryForTenant('tenant-alfa'),
};

export const TenantBeta: Story = {
  name: 'Tenant Beta',
  args: { tenant: 'tenant-beta', children: 'Continuar (Beta)' },
  parameters: { tenant: 'tenant-beta' },
  play: playStoryForTenant('tenant-beta'),
};
