import type { Meta, StoryObj } from '@storybook/react';

import { DataStateSkeleton } from './DataStateSkeleton';

const meta: Meta<typeof DataStateSkeleton> = {
  title: 'Shared/UI/Data States/Skeleton',
  component: DataStateSkeleton,
  parameters: {
    layout: 'centered',
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

