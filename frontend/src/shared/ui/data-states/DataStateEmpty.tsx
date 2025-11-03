import type { HTMLAttributes, ReactNode } from 'react';

import { cn } from '../../lib/cn';

export interface DataStateEmptyProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Título do estado vazio, normalmente uma frase curta.
   */
  title: string;
  /**
   * Descrição com instruções ou contexto adicional.
   */
  description: string;
  /**
   * Ação opcional (botão, link). Deve ser um elemento interativo acessível.
   */
  action?: ReactNode;
  /**
   * Ícone ilustrativo, sempre tratado como decorativo.
   */
  icon?: ReactNode;
}

export const DataStateEmpty = ({
  title,
  description,
  action,
  icon,
  className,
  ...rest
}: DataStateEmptyProps) => (
  <div
    {...rest}
    role="status"
    aria-live="polite"
    className={cn(
      'flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-border bg-surface px-8 py-10 text-center',
      className,
    )}
  >
    {icon ? (
      <span className="text-4xl text-brand-primary" aria-hidden="true">
        {icon}
      </span>
    ) : null}
    <div className="space-y-2">
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
      <p className="text-sm text-text-secondary max-w-prose">{description}</p>
    </div>
    {action ? <div className="mt-2 flex flex-wrap justify-center gap-2">{action}</div> : null}
  </div>
);

