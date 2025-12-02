# Design System Tokens

> **Status**: v1.0 · aprovado em 2025-10-16 · Owners: DS Guild & Frontend Foundation  
> **Referências**: `BLUEPRINT_ARQUITETURAL.md §4`, `specs/001-indice-features-template/spec.md`, `specs/002-f-10-fundacao/spec.md`, Constituição v5.2.0 (Art. I, IX, XIII), `adicoes_blueprint.md` itens 1, 2 e 13.

## 1. Objetivo e Escopo

Este documento oficializa o catálogo de tokens do design system do IABANK, padronizando cores, tipografia, espaçamento, raios, elevação, transições e z-index para uso em todos os produtos frontend desenvolvidos em **React + Vite + Tailwind CSS** (Blueprint §4, Constituição Art. I).  
Os tokens são a base para theming multi-tenant (`tenant-default`, `tenant-alfa`, `tenant-beta`) e sustentam:
- Storybook/Chromatic com cobertura visual ≥95% por tenant (`specs/002-f-10-fundacao/spec.md`).
- Lint de arquitetura (governança de imports, FSD) e validação de acessibilidade WCAG 2.2 AA.
- Propagação consistente para contratos (`shared/ui`), features FSD e pactos FE/BE.

## 2. Taxonomia de Tokens

| Camada | Descrição | Exemplos | Observações |
|--------|-----------|----------|-------------|
| **Fundacionais** | Valores físicos sem contexto de UI. | `color.brand.primary.default`, `space.6`, `radius.lg`, `shadow.md`. | São definidos por tenant sempre que houver variação de branding. |
| **Semânticos** | Alias usados pela camada de UI. | `surface.background`, `text.muted`, `status.success.bg`. | Devem apontar para fundacionais e garantir contraste AA. |
| **Componentes** | Ajustes específicos (botão, card, input). | `button.primary.bg`, `card.surface`. | Mantidos em `shared/ui` para evitar dispersão em features. |

A governança segue a política de mudanças descrita na seção 8; qualquer alteração fundacional exige revisão de acessibilidade e atualização do snapshot Chromatic.

## 3. Implementação de Referência (React + Vite + Tailwind CSS)

### 3.1 Estrutura FSD
- `src/shared/config/theme/tenants.ts`: valores fundacionais por tenant, gerados a partir de JSON.
- `src/shared/config/theme/semantic.ts`: mapeia alias semânticos (variam por tenant via CSS vars).
- Carregamento dinâmico dos tokens JSON em runtime (`registry.ts`), aplicando CSS custom properties no `<html data-tenant="...">` sem materializar CSS global por tenant.
- Consumo nos componentes via `className` Tailwind (com fallback do tenant default) ou `style` por CSS vars, mantendo os imports limitados a `shared/ui` (governança FSD).

### 3.2 CSS Variables + Tailwind

```ts
// tailwind.config.ts (Vite)
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "tailwindcss";

export default defineConfig({
  plugins: [react(), tailwind()],
});
```

```ts
// tailwind.config.ts
import { defineConfig } from "tailwindcss";
import { tenantTokens } from "./src/shared/config/theme/tenants";

const tokens = tenantTokens["tenant-default"];

export default defineConfig({
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Usa CSS vars geradas em runtime; valores do tenant default servem como fallback seguro.
      colors: {
        brand: {
          primary: "var(--color-brand-primary, ${tokens.foundation['color.brand.primary']})",
        },
      },
      spacing: Object.fromEntries(
        Object.entries(tokens.foundation)
          .filter(([key]) => key.startsWith("space."))
          .map(([key, value]) => [key.replace("space.", ""), `var(--${key.replace(/\./g, "-")}, ${value})`])
      ),
      // Demais mapas seguem a mesma lógica (radius, shadows, fontSize/lineHeight etc).
    },
  },
  plugins: [],
});
```

```ts
// src/shared/config/theme/tenants.ts (trecho ilustrativo)
export const tenants = {
  "tenant-default": {
    "color-brand-primary": "#1E3A8A",
    "color-brand-primary-on": "#F8FAFC",
    "color-background-default": "#F8FAFC",
    // ...
  },
  "tenant-alfa": {
    "color-brand-primary": "#0F766E",
    // ...
  },
  "tenant-beta": {
    "color-brand-primary": "#7C3AED",
    // ...
  },
} as const;
```

As variáveis são aplicadas no `<html>` com `data-tenant="tenant-default"`; alterações dinâmicas entram via Zustand + TanStack Query conforme a jornada multi-tenant.

## 4. Tokens de Cor

Todos os pares foreground/background cumprem contraste mínimo 4.5:1 (WCAG 2.2 AA). Valores em hexadecimal; para animações específicas pode-se converter para HSL/OKLCH sem alterar o valor perceptivo.

### 4.1 Paleta Base por Tenant

| Token | Uso | tenant-default | tenant-alfa | tenant-beta |
|-------|-----|----------------|-------------|-------------|
| `color.brand.primary` | Ações principais, CTA, slider ativo | `#1E3A8A` | `#0F766E` | `#7C3AED` |
| `color.brand.on-primary` | Texto/ícones sobre primária | `#F8FAFC` | `#F0FDFA` | `#F5F3FF` |
| `color.brand.secondary` | Destaques complementares, tabs | `#0EA5E9` | `#65A30D` | `#38BDF8` |
| `color.brand.on-secondary` | Texto/ícones sobre secundária | `#0F172A` | `#052E16` | `#0C4A6E` |
| `color.background.default` | Page shell, layout base | `#F8FAFC` | `#F0FDF4` | `#F5F3FF` |
| `color.background.alt` | Seções alternadas | `#E2E8F0` | `#DCFCE7` | `#EDE9FE` |
| `color.surface.default` | Cards, modais, dropdowns | `#FFFFFF` | `#FFFFFF` | `#FFFFFF` |
| `color.surface.inverse` | Barra lateral escura, footer | `#0F172A` | `#064E3B` | `#1E1B4B` |
| `color.text.primary` | Títulos, textos principais | `#0F172A` | `#052E16` | `#1E1B4B` |
| `color.text.secondary` | Texto de apoio | `#475569` | `#1C4532` | `#3F3D56` |
| `color.text.muted` | Labels, placeholders | `#64748B` | `#3F624F` | `#6B6684` |
| `color.border.default` | Borda padrão | `#CBD5F5` | `#86EFAC` | `#C4B5FD` |

### 4.2 Estados e Feedback (comuns aos tenants)

| Token | Background | On Color | Uso |
|-------|------------|----------|-----|
| `status.success.bg` | `#15803D` | `#F0FDF4` | Toasts, badges de sucesso |
| `status.warning.bg` | `#B45309` | `#FFFBEB` | Avisos, banners de risco médio |
| `status.danger.bg` | `#B91C1C` | `#FEF2F2` | Erros críticos, destructives |
| `status.info.bg` | `#0369A1` | `#E0F2FE` | Feedback informativo |
| `status.neutral.bg` | `#0F172A0D` | `#0F172A` | Estados neutros, skeleton |

### 4.3 Paleta para Gráficos

| Token | tenant-default | tenant-alfa | tenant-beta |
|-------|----------------|-------------|-------------|
| `chart.1` | `#2563EB` | `#0EA5E9` | `#7C3AED` |
| `chart.2` | `#F97316` | `#65A30D` | `#F59E0B` |
| `chart.3` | `#10B981` | `#22C55E` | `#C084FC` |
| `chart.4` | `#EC4899` | `#F97316` | `#38BDF8` |
| `chart.5` | `#8B5CF6` | `#14B8A6` | `#F472B6` |

## 5. Tipografia

- **Famílias**  
  - `font.sans`: `"Geist Sans", "Inter", "Segoe UI", system`  
  - `font.mono`: `"Geist Mono", "Fira Code", "SFMono-Regular", monospace`
- **Pesos** (`font.weight`)  
  - `light`: 300 · `regular`: 400 · `medium`: 500 · `semibold`: 600 · `bold`: 700
- **Escala tipográfica**

| Token | Rem | Px (base 16) | Line height | Uso |
|-------|-----|--------------|-------------|-----|
| `font.size.xs` | `0.75` | 12 | `1.125rem` | Labels, legendas |
| `font.size.sm` | `0.875` | 14 | `1.25rem` | Texto secundário |
| `font.size.base` | `1` | 16 | `1.5rem` | Corpo de texto |
| `font.size.lg` | `1.125` | 18 | `1.75rem` | Destaques pequenos |
| `font.size.xl` | `1.25` | 20 | `1.85rem` | Subtítulos |
| `font.size.2xl` | `1.5` | 24 | `2rem` | Títulos em cards |
| `font.size.3xl` | `1.875` | 30 | `2.25rem` | Headings de seção |
| `font.size.4xl` | `2.25` | 36 | `2.5rem` | Headline hero |
| `font.size.5xl` | `3` | 48 | `1.05` | Destaques hero |

## 6. Espaçamento e Layout

- **Escala de espaçamento (`space.N`)**

| Token | Rem | Px | Uso típico |
|-------|-----|----|------------|
| `space.0` | 0 | 0 | Reset |
| `space.1` | 0.25 | 4 | Gap apertado |
| `space.2` | 0.5 | 8 | Padding interno pequeno |
| `space.3` | 0.75 | 12 | Gap entre label/input |
| `space.4` | 1 | 16 | Layout base |
| `space.5` | 1.5 | 24 | Cards compactos |
| `space.6` | 2 | 32 | Containers médios |
| `space.7` | 2.5 | 40 | Seções |
| `space.8` | 3 | 48 | Hero/top spacing |
| `space.9` | 4 | 64 | Estruturas amplas |
| `space.10` | 5 | 80 | Páginas |
| `space.11` | 6 | 96 | Margens generosas |
| `space.12` | 8 | 128 | Quebras hero |

- **Larguras de borda (`border.width`)**  
  - `hairline`: `1px` · `thin`: `1.5px` · `base`: `2px` · `thick`: `4px`

- **Raios (`radius`)**

| Token | Valor | Uso |
|-------|-------|-----|
| `radius.none` | `0px` | Listas densas, tabelas compactas |
| `radius.xs` | `2px` | Badges discretos |
| `radius.sm` | `4px` | Inputs |
| `radius.md` | `6px` | Botões padrão |
| `radius.lg` | `10px` | Cards, modais |
| `radius.xl` | `16px` | Componentes destacados |
| `radius.full` | `9999px` | Avatares, toggles |

## 7. Elevação, Transições e Camadas

- **Sombras (`shadow`)**

| Token | Valor | Uso |
|-------|-------|-----|
| `shadow.sm` | `0 1px 2px rgba(15, 23, 42, 0.08)` | Hover leve |
| `shadow.md` | `0 4px 8px rgba(15, 23, 42, 0.12)` | Cards |
| `shadow.lg` | `0 12px 20px rgba(15, 23, 42, 0.16)` | Modais, popovers |
| `shadow.focus` | `0 0 0 3px rgba(30, 58, 138, 0.35)` | Acessibilidade (outline) |

- **Transições (`transition.duration`, `transition.timing`)**

| Token | Duração | Uso |
|-------|---------|-----|
| `transition.fast` | `150ms` | Hovers, focus |
| `transition.base` | `200ms` | Estados de botão |
| `transition.slow` | `300ms` | Modais, off-canvas |
| `transition.timing.standard` | `cubic-bezier(0.4, 0, 0.2, 1)` | Movimento padrão |
| `transition.timing.decelerate` | `cubic-bezier(0, 0, 0.2, 1)` | Entradas |
| `transition.timing.accelerate` | `cubic-bezier(0.4, 0, 1, 1)` | Saídas |

- **Z-index (`layer`)**

| Token | Valor | Uso |
|-------|-------|-----|
| `layer.content` | `0` | Fluxo padrão |
| `layer.dropdown` | `1000` | Menus suspensos |
| `layer.sticky` | `1020` | Headers fixos |
| `layer.overlay` | `1040` | Overlays simples |
| `layer.modal` | `1060` | Diálogos |
| `layer.popover` | `1080` | Tooltips/Popovers |
| `layer.toast` | `1100` | Toasts/Sonner |

## 8. Fallback, Acessibilidade e Governança

- **Fallback multi-tenant**: ausência de configuração aplica `tenant-default`, com alerta automático no backlog de branding (Spec F-10 – FR-004).  
- **WCAG**: alterações de cor exigem relatório de contraste anexado à PR (`pnpm ui:a11y-check`).  
- **Observabilidade**: mudanças de tokens devem atualizar as tags OTEL `component.theme` e `component.tenant` nos eventos de UI.
- **Chromatic/Storybook**: qualquer alteração exige rebuild dos snapshots todos os tenants (`pnpm storybook:test --tenants all`) garantindo cobertura ≥95% por tenant.
- **CSP/Trusted Types**: tokens não podem injetar conteúdo dinâmico; uso limitado a CSS e configurações serializadas (Constituição Art. XIII).

## 9. Processo de Mudança

1. Abrir issue `Design System Update` com descrição, impacto em tenants e evidências de contraste.  
2. Executar matriz de testes: `lint`, `storybook`, `chromatic`, `ui:a11y-check`.  
3. Atualizar pactos visuais e publicar changelog no pacote UI compartilhado.  
4. Registrar alteração nesta seção (histórico) e referenciar PR correspondente.

## 10. Histórico

| Data | Versão | Descrição | Referência |
|------|--------|-----------|------------|
| 2025-10-11 | 0.1 (placeholder) | Placeholder provisório criado para destravar `specs/002-f-10-fundacao/spec.md`. | PR TBD |
| 2025-10-16 | 1.0 | Guia definitivo multi-tenant alinhado ao blueprint (cores, tipografia, spacing, sombras, transições, governança). | PR TBD |

---

> Para dúvidas adicionais ou necessidades de novos tenants, registrar no `/clarify` conforme fluxo Spec-Kit.
