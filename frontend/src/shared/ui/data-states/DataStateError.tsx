import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react';

import { cn } from '../../lib/cn';
import { Button } from '../button';

export interface DataStateErrorProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Título exibido no topo do alerta.
   * @default 'Ocorreu um erro'
   */
  title?: string;
  /**
   * Mensagem com detalhes sobre o erro ou orientação de próxima ação.
   */
  message: string;
  /**
   * Ação de retry para erros recuperáveis.
   */
  onRetry?: () => void;
  /**
   * Texto exibido no botão de retry.
   * @default 'Tentar novamente'
   */
  retryLabel?: string;
  /**
   * Conteúdo adicional (ex.: link para suporte).
   */
  action?: ReactNode;
  /**
   * Personaliza o tipo do botão de retry (ex.: submit em formulários).
   */
  retryButtonType?: ButtonHTMLAttributes<HTMLButtonElement>['type'];
}

export const DataStateError = ({
  title = 'Ocorreu um erro',
  message,
  onRetry,
  retryLabel = 'Tentar novamente',
  action,
  retryButtonType = 'button',
  className,
  ...rest
}: DataStateErrorProps) => (
  <div
    {...rest}
    role="alert"
    aria-live="assertive"
    className={cn(
      'rounded-lg border border-status-danger bg-surface px-6 py-5 text-left shadow-sm',
      className,
    )}
  >
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-4">
      <span
        aria-hidden="true"
        className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-status-danger text-status-danger-foreground font-semibold"
      >
        !
      </span>
      <div className="flex-1 space-y-2">
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-text-primary">{title}</h3>
          <p className="text-sm text-text-secondary">{message}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {onRetry ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={onRetry}
              type={retryButtonType}
              data-testid="retry-button"
            >
              {retryLabel}
            </Button>
          ) : null}
          {action}
        </div>
      </div>
    </div>
  </div>
);
