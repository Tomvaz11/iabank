import type { PropsWithChildren, ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';

const Providers = ({ children }: PropsWithChildren): JSX.Element => {
  return <>{children}</>;
};

export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => {
  return render(ui, { wrapper: Providers, ...options });
};

export * from '@testing-library/react';
