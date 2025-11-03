import type { Meta, StoryObj } from '@storybook/react';

import { Button } from '../button';
import { DataStateEmpty } from './DataStateEmpty';

const meta: Meta<typeof DataStateEmpty> = {
  title: 'Shared/UI/Data States/Empty',
  component: DataStateEmpty,
  parameters: {
    layout: 'centered',
  },
  args: {
    title: 'Nenhum resultado encontrado',
    description: 'Ajuste os filtros ou crie um novo item para começar.',
    icon: <span className="text-4xl">✨</span>,
    action: (
      <Button size="sm" variant="primary">
        Criar item
      </Button>
    ),
  },
};

export default meta;

type Story = StoryObj<typeof DataStateEmpty>;

export const Default: Story = {};

export const SemAcao: Story = {
  args: {
    action: undefined,
  },
};
