import { describe, expect, it, vi } from 'vitest';

import {
  fireEvent,
  renderWithProviders,
  screen,
} from '../../../tests/utils/test-utils';
import { Button } from '../button';
import {
  DataStateEmpty,
  DataStateError,
  DataStateSkeleton,
} from './index';

describe('@SC-004 componentes de estado de dados', () => {
  it('renderiza skeleton com avatar e número de linhas configurável', () => {
    renderWithProviders(<DataStateSkeleton lines={4} showAvatar />);

    const skeleton = screen.getByRole('status', { name: 'Carregando conteúdo' });
    expect(skeleton).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByTestId('data-state-skeleton-avatar')).toBeInTheDocument();
    expect(screen.getAllByTestId('data-state-skeleton-line')).toHaveLength(4);
  });

  it('exibe estado vazio com título, descrição e ação', () => {
    renderWithProviders(
      <DataStateEmpty
        title="Nenhum dado"
        description="Adicione um novo item para começar."
        action={
          <Button size="sm" variant="primary">
            Adicionar item
          </Button>
        }
        icon={<span className="text-3xl">📄</span>}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Nenhum dado' })).toBeInTheDocument();
    expect(screen.getByText('Adicione um novo item para começar.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Adicionar item' })).toBeInTheDocument();
  });

  it('aciona retry e ações extras em erros recuperáveis', () => {
    const retrySpy = vi.fn();
    const supportSpy = vi.fn();

    renderWithProviders(
      <DataStateError
        message="Falha ao se conectar com o servidor."
        onRetry={retrySpy}
        retryLabel="Tentar novamente"
        action={
          <Button size="sm" variant="secondary" onClick={supportSpy}>
            Abrir suporte
          </Button>
        }
      />,
    );

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }));
    expect(retrySpy).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Abrir suporte' }));
    expect(supportSpy).toHaveBeenCalledTimes(1);
  });
});

