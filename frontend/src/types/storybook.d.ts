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
  export const expect: any;
  export const within: any;
  export const userEvent: any;
}
