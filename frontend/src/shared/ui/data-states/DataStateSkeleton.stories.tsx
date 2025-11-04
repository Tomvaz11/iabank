import type { Meta, StoryObj } from '@storybook/react';

import { DataStateSkeleton } from './DataStateSkeleton';

const meta: Meta<typeof DataStateSkeleton> = {
  title: 'Shared/UI/Data States/Skeleton',
  component: DataStateSkeleton,
  parameters: {
    layout: 'centered',
    tenants: ['tenant-default', 'tenant-alfa', 'tenant-beta'],
  },
  args: {
    lines: 3,
    showAvatar: true,
  },
};

export default meta;

type Story = StoryObj<typeof DataStateSkeleton>;

export const Default: Story = {};

export const WithoutAvatar: Story = {
  args: {
    showAvatar: false,
    lines: 5,
  },
};

// Variações por tenant para cobertura visual (Chromatic)
export const TenantDefault: Story = {
  name: 'Tenant default',
  parameters: { tenant: 'tenant-default' },
};

export const TenantAlfa: Story = {
  name: 'Tenant Alfa',
  parameters: { tenant: 'tenant-alfa' },
};

export const TenantBeta: Story = {
  name: 'Tenant Beta',
  parameters: { tenant: 'tenant-beta' },
};
