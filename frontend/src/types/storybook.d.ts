declare module '@storybook/react' {
  import type { ReactNode } from 'react';

  export type Meta<TArgs = unknown> = {
    title: string;
    component?: unknown;
    render?: (args: TArgs) => ReactNode;
    args?: Partial<TArgs>;
    parameters?: Record<string, unknown>;
    argTypes?: Record<string, unknown>;
  };

  export type StoryObj<TArgs = Record<string, unknown>> = {
    name?: string;
    args?: Partial<TArgs>;
    parameters?: Record<string, unknown>;
    render?: (args: TArgs) => ReactNode;
    play?: (context: {
      canvasElement: HTMLElement;
      args: TArgs;
    }) => Promise<void> | void;
  };
}

declare module '@storybook/test' {
  import type { expect as vitestExpect } from 'vitest';
  import type { within as testingLibraryWithin } from '@testing-library/react';
  import type { userEvent as testingLibraryUserEvent } from '@testing-library/user-event';

  export const expect: typeof vitestExpect;
  export const within: typeof testingLibraryWithin;
  export const userEvent: typeof testingLibraryUserEvent;
}
