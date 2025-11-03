import type { Meta, StoryObj } from '@storybook/react';

import { Button } from '../button';
import { DataStateError } from './DataStateError';

const meta: Meta<typeof DataStateError> = {
  title: 'Shared/UI/Data States/Error',
  component: DataStateError,
  parameters: {
    layout: 'centered',
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

