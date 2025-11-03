import { forwardRef } from 'react';
import type {
  ButtonHTMLAttributes,
  CSSProperties,
  PropsWithChildren,
  ReactNode,
} from 'react';

import { cn } from '../../lib/cn';

export type ButtonVariant = 'primary' | 'secondary';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'type'> {
  /**
   * Variante visual. `primary` utiliza tokens específicos por tenant,
   * enquanto `secondary` aplica contraste seguro sobre superfícies neutras.
   */
  variant?: ButtonVariant;
  /**
   * Tamanho do botão. Controla tipografia e espaçamento.
   */
  size?: ButtonSize;
  /**
   * Ocupa toda a largura disponível do contêiner.
   */
  fullWidth?: boolean;
  /**
   * Indica carregamento, exibindo spinner e bloqueando interações.
   */
  isLoading?: boolean;
  /**
   * Ícone exibido antes do conteúdo.
   */
  leadingIcon?: ReactNode;
  /**
   * Ícone exibido após o conteúdo.
   */
  trailingIcon?: ReactNode;
  /**
   * Tipo do botão; `button` é aplicado por padrão para evitar submits acidentais.
   */
  type?: ButtonHTMLAttributes<HTMLButtonElement>['type'];
}

const BASE_CLASSES =
  'inline-flex items-center justify-center gap-2 font-medium rounded-md transition duration-base ease-standard focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2 focus-visible:ring-offset-surface disabled:cursor-not-allowed disabled:opacity-60';

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-component-button-primary text-component-button-primary-foreground border border-component-button-primary shadow-button-primary hover:bg-component-button-primary-hover',
  secondary:
    'bg-surface text-brand-primary border border-brand-primary shadow-sm hover:bg-brand-primary hover:text-brand-primary-foreground',
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm sm:text-base',
  lg: 'px-5 py-3 text-base sm:text-lg',
};

const SPINNER_SIZE: Record<ButtonSize, string> = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

const Spinner = ({ size }: { size: ButtonSize }) => (
  <span
    aria-hidden="true"
    className={cn(
      'animate-spin rounded-full border-2 border-current border-r-transparent',
      SPINNER_SIZE[size],
    )}
  />
);

const ButtonInner = ({
  children,
  isLoading,
  size,
  leadingIcon,
  trailingIcon,
}: PropsWithChildren<
  Pick<ButtonProps, 'isLoading' | 'size' | 'leadingIcon' | 'trailingIcon'>
>) => (
  <span className="inline-flex items-center justify-center gap-2">
    {(isLoading || leadingIcon) && (
      <span className="inline-flex items-center" aria-hidden={!isLoading}>
        {isLoading ? <Spinner size={size ?? 'md'} /> : leadingIcon}
      </span>
    )}
    <span className="inline-flex items-center justify-center whitespace-nowrap">
      {children}
    </span>
    {trailingIcon && (
      <span className="inline-flex items-center" aria-hidden="true">
        {trailingIcon}
      </span>
    )}
  </span>
);

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      isLoading = false,
      leadingIcon,
      trailingIcon,
      className,
      children,
      disabled,
      type,
      style: inlineStyle,
      ...rest
    },
    ref,
  ) => {
    const isDisabled = disabled ?? false;
    const computedType = type ?? 'button';
    const styleOverrides: CSSProperties = {};

    if (variant === 'primary') {
      styleOverrides.backgroundColor = 'var(--button-primary-bg, #1E3A8A)';
      styleOverrides.color = 'var(--button-primary-text, #F8FAFC)';
      styleOverrides.borderColor = 'var(--button-primary-border, #1E3A8A)';
      styleOverrides.boxShadow = 'var(--button-primary-shadow, 0 1px 2px rgba(15, 23, 42, 0.08))';
    }

    return (
      <button
        {...rest}
        ref={ref}
        type={computedType}
        className={cn(
          BASE_CLASSES,
          VARIANT_CLASSES[variant],
          SIZE_CLASSES[size],
          fullWidth && 'w-full',
          isLoading && 'cursor-wait',
          className,
        )}
        data-variant={variant}
        disabled={isDisabled || isLoading}
        aria-busy={isLoading || undefined}
        style={{
          ...styleOverrides,
          ...inlineStyle,
        }}
      >
        <ButtonInner
          isLoading={isLoading}
          size={size}
          leadingIcon={leadingIcon}
          trailingIcon={trailingIcon}
        >
          {children}
        </ButtonInner>
      </button>
    );
  },
);

Button.displayName = 'Button';

export const BUTTON_VARIANTS: readonly ButtonVariant[] = ['primary', 'secondary'] as const;
export const BUTTON_SIZES: readonly ButtonSize[] = ['sm', 'md', 'lg'] as const;
