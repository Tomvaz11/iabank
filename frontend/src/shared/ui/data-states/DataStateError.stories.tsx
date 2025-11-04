import type { Meta, StoryObj } from '@storybook/react';

import { Button } from '../button';
import { DataStateError } from './DataStateError';

const meta: Meta<typeof DataStateError> = {
  title: 'Shared/UI/Data States/Error',
  component: DataStateError,
  parameters: {
    layout: 'centered',
    tenants: ['tenant-default', 'tenant-alfa', 'tenant-beta'],
  },
  args: {
    title: 'Não foi possível carregar os dados',
    message:
      'Verifique sua conexão com a internet e tente novamente. Persistindo o erro, entre em contato com o suporte.',
    onRetry: () => undefined,
    action: (
      <Button variant="secondary" size="sm">
        Abrir suporte
      </Button>
    ),
  },
};

export default meta;

type Story = StoryObj<typeof DataStateError>;

export const Default: Story = {};

export const SemRetry: Story = {
  args: {
    onRetry: undefined,
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
