import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders, fireEvent, screen } from '../../../tests/utils/test-utils';
import { Button } from './Button';

describe('@SC-002 componente shared/ui/Button', () => {
  it('usa type="button" por padrão e respeita o ref repassado', () => {
    const focusSpy = vi.fn();
    const Component = () => (
      <Button ref={(element) => element && focusSpy(element)} data-testid="primary-button">
        Ação
      </Button>
    );

    renderWithProviders(<Component />);
    const button = screen.getByTestId('primary-button');

    expect(button).toHaveAttribute('type', 'button');
    expect(button).toHaveAttribute('data-variant', 'primary');
    expect(button).toHaveClass('bg-component-button-primary');
    expect(focusSpy).toHaveBeenCalledWith(button);
  });

  it('aplica largura total e tamanho configurado', () => {
    renderWithProviders(
      <Button data-testid="secondary" variant="secondary" size="lg" fullWidth>
        Continuar
      </Button>,
    );

    const button = screen.getByTestId('secondary');
    expect(button.dataset.variant).toBe('secondary');
    expect(button).toHaveClass('px-5');
    expect(button).toHaveClass('w-full');
    expect(button).toHaveClass('hover:text-brand-primary-foreground');
  });

  it('exibe spinner acessível e bloqueia interações durante carregamento', () => {
    const onClick = vi.fn();

    renderWithProviders(
      <Button isLoading onClick={onClick}>
        Salvar
      </Button>,
    );

    const button = screen.getByRole('button', { name: 'Salvar' });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');

    fireEvent.click(button);
    expect(onClick).not.toHaveBeenCalled();
  });
});
