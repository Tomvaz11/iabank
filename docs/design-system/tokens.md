# Design System Tokens (Provisório)

> **Status**: Placeholder inicial criado em 2025-10-11; deve ser substituído pelo guia definitivo após conclusão da normalização do design system.

## Objetivo

Documentar, de forma temporária, a estrutura mínima de tokens Tailwind CSS para tenants multi-tenant do IABANK até que o guia oficial seja consolidado.

## Estrutura Sugerida

- `colors`: mapa de cores por tenant (`default`, `alfa`, `beta`), incluindo primária, secundária, fundo, alerta, sucesso e texto (tons claro/escuro).
- `typography`: famílias tipográficas, pesos e tamanhos base (rem) alinhados ao Blueprint §4.
- `spacing`: escala base (0-12) em rem, garantindo consistência com componentes compartilhados.
- `radius`: raios padronizados (`none`, `sm`, `md`, `lg`, `full`) utilizados em botões, cards e modais.
- `zIndex`: camadas principais (`dropdown`, `modal`, `toast`) para evitar conflitos entre tenants.

## Próximos Passos

1. Detalhar tokens adicionais (bordas, sombras, transições) conforme componentes do design system forem migrados.
2. Validar contrastes conforme WCAG 2.2 AA para cada tenant.
3. Registrar histórico da evolução deste documento e apontar a versão final no `specs/002-f-10-fundacao/spec.md` assim que disponível.
