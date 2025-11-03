import type { Config } from 'tailwindcss';

import { tenantTokens } from './src/shared/config/theme/tenants';

const DEFAULT_TENANT = 'tenant-default';

const defaultTokens = tenantTokens[DEFAULT_TENANT];
const foundation = defaultTokens.foundation;
const semantic = defaultTokens.semantic;
const component = defaultTokens.component;

const FONT_SCALE = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl'] as const;

const toVarName = (token: string): string => `--${token.replace(/\./g, '-')}`;

const cssVar = (token: string, fallback: string): string => `var(${toVarName(token)}, ${fallback})`;

const requireToken = (source: Record<string, string>, token: string): string => {
  const value = source[token];
  if (value === undefined) {
    throw new Error(`Token "${token}" não encontrado para o tenant padrão.`);
  }
  return value;
};

const spacing = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('space.'))
    .map(([token, value]) => [token.replace('space.', ''), cssVar(token, value)]),
);

const borderRadius = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('radius.'))
    .map(([token, value]) => [token.replace('radius.', ''), cssVar(token, value)]),
);

const borderWidth = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('border.width.'))
    .map(([token, value]) => [token.replace('border.width.', ''), cssVar(token, value)]),
);

const boxShadow = {
  ...Object.fromEntries(
    Object.entries(foundation)
      .filter(([token]) => token.startsWith('shadow.') && token !== 'shadow.focus')
      .map(([token, value]) => [token.replace('shadow.', ''), cssVar(token, value)]),
  ),
  focus: cssVar('shadow.focus', requireToken(foundation, 'shadow.focus')),
  'button-primary': cssVar('button.primary.shadow', requireToken(component, 'button.primary.shadow')),
};

const transitionDuration = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('transition.') && !token.startsWith('transition.timing.'))
    .map(([token, value]) => [token.replace('transition.', ''), cssVar(token, value)]),
);

const transitionTimingFunction = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('transition.timing.'))
    .map(([token, value]) => [token.replace('transition.timing.', ''), cssVar(token, value)]),
);

const zIndex = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('layer.'))
    .map(([token, value]) => [token.replace('layer.', ''), cssVar(token, value)]),
);

const fontWeight = Object.fromEntries(
  Object.entries(foundation)
    .filter(([token]) => token.startsWith('font.weight.'))
    .map(([token, value]) => [token.replace('font.weight.', ''), cssVar(token, value)]),
);

const fontFamily = {
  sans: cssVar('font.family.sans', requireToken(foundation, 'font.family.sans')),
  mono: cssVar('font.family.mono', requireToken(foundation, 'font.family.mono')),
};

const fontSize = Object.fromEntries(
  FONT_SCALE.map((scale) => {
    const baseToken = `font.size.${scale}`;
    const lineHeightToken = `font.lineHeight.${scale}`;
    const sizeValue = requireToken(foundation, baseToken);
    const lineHeightValue = requireToken(foundation, lineHeightToken);
    return [
      scale,
      [
        cssVar(baseToken, sizeValue),
        {
          lineHeight: cssVar(lineHeightToken, lineHeightValue),
        },
      ],
    ];
  }),
) as Record<string, [string, { lineHeight: string }]>;

const colors = {
  brand: {
    primary: cssVar('color.brand.primary', requireToken(foundation, 'color.brand.primary')),
    'primary-foreground': cssVar('color.brand.on-primary', requireToken(foundation, 'color.brand.on-primary')),
    secondary: cssVar('color.brand.secondary', requireToken(foundation, 'color.brand.secondary')),
    'secondary-foreground': cssVar(
      'color.brand.on-secondary',
      requireToken(foundation, 'color.brand.on-secondary'),
    ),
  },
  background: {
    DEFAULT: cssVar('color.background.default', requireToken(foundation, 'color.background.default')),
    alt: cssVar('color.background.alt', requireToken(foundation, 'color.background.alt')),
  },
  surface: {
    DEFAULT: cssVar('color.surface.default', requireToken(foundation, 'color.surface.default')),
    inverse: cssVar('color.surface.inverse', requireToken(foundation, 'color.surface.inverse')),
  },
  text: {
    primary: cssVar('color.text.primary', requireToken(foundation, 'color.text.primary')),
    secondary: cssVar('color.text.secondary', requireToken(foundation, 'color.text.secondary')),
    muted: cssVar('color.text.muted', requireToken(foundation, 'color.text.muted')),
  },
  border: {
    DEFAULT: cssVar('color.border.default', requireToken(foundation, 'color.border.default')),
  },
  status: {
    success: cssVar('status.success.bg', requireToken(semantic, 'status.success.bg')),
    'success-foreground': cssVar('status.success.on', requireToken(semantic, 'status.success.on')),
    warning: cssVar('status.warning.bg', requireToken(semantic, 'status.warning.bg')),
    'warning-foreground': cssVar('status.warning.on', requireToken(semantic, 'status.warning.on')),
    danger: cssVar('status.danger.bg', requireToken(semantic, 'status.danger.bg')),
    'danger-foreground': cssVar('status.danger.on', requireToken(semantic, 'status.danger.on')),
    info: cssVar('status.info.bg', requireToken(semantic, 'status.info.bg')),
    'info-foreground': cssVar('status.info.on', requireToken(semantic, 'status.info.on')),
    neutral: cssVar('status.neutral.bg', requireToken(semantic, 'status.neutral.bg')),
    'neutral-foreground': cssVar('status.neutral.on', requireToken(semantic, 'status.neutral.on')),
  },
  component: {
    'button-primary': cssVar('button.primary.bg', requireToken(component, 'button.primary.bg')),
    'button-primary-foreground': cssVar('button.primary.text', requireToken(component, 'button.primary.text')),
    'button-primary-border': cssVar('button.primary.border', requireToken(component, 'button.primary.border')),
    'button-primary-hover': cssVar('button.primary.hover', requireToken(component, 'button.primary.hover')),
    'button-primary-focus': cssVar('button.primary.focus', requireToken(component, 'button.primary.focus')),
  },
};

const config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors,
      spacing,
      borderRadius,
      borderWidth,
      boxShadow,
      fontFamily,
      fontWeight,
      fontSize,
      transitionDuration,
      transitionTimingFunction,
      zIndex,
      ringColor: {
        focus: cssVar('focus.ring', requireToken(semantic, 'focus.ring')),
      },
    },
  },
  plugins: [],
} satisfies Config;

export default config;
