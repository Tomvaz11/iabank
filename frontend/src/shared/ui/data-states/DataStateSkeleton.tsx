import type { HTMLAttributes } from 'react';

import { cn } from '../../lib/cn';

export interface DataStateSkeletonProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Quantidade de linhas exibidas após o avatar opcional.
   */
  lines?: number;
  /**
   * Exibe placeholder circular, útil para listas com avatar.
   */
  showAvatar?: boolean;
}

const createSkeletonLines = (count: number) =>
  Array.from({ length: Math.max(1, count) }, (_, index) => {
    const key = `skeleton-line-${index}`;
    const widthClass =
      index === 0 ? 'w-full' : index === count - 1 ? 'w-2/3' : 'w-[85%]';
    return (
      <div
        key={key}
        data-testid="data-state-skeleton-line"
        className={cn(
          'h-3 rounded-full bg-border opacity-60',
          widthClass,
        )}
      />
    );
  });

export const DataStateSkeleton = ({
  className,
  lines = 3,
  showAvatar = false,
  ...rest
}: DataStateSkeletonProps) => {
  return (
    <div
      {...rest}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="Carregando conteúdo"
      className={cn(
        'animate-pulse space-y-4 rounded-lg border border-dashed border-border bg-surface px-4 py-6',
        className,
      )}
    >
      {showAvatar && (
        <div className="flex items-center gap-3">
          <div
            className="h-10 w-10 rounded-full bg-border opacity-60"
            data-testid="data-state-skeleton-avatar"
          />
          <div className="flex-1 space-y-2">
            <div className="h-3 rounded-full bg-border opacity-60" />
            <div className="h-3 w-3/4 rounded-full bg-border opacity-60" />
          </div>
        </div>
      )}
      <div className="space-y-2">{createSkeletonLines(lines)}</div>
      <span className="sr-only">Carregando conteúdo</span>
    </div>
  );
};
