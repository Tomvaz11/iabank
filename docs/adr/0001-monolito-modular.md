# 0001. Monolito Modular vs Microserviços

**Status**: Accepted
**Date**: 2025-09-12
**Authors**: Equipe IABANK

## Context

Precisávamos decidir entre arquitetura de microserviços ou monolito para o IABANK, uma plataforma SaaS para gestão de empréstimos. A decisão afeta diretamente a complexidade de desenvolvimento, deploy e manutenção do sistema.

## Decision

Optamos por Monolito Modular com Django Apps bem definidos e isolamento de domínio claro.

## Rationale

- **Equipe pequena**: No início do projeto temos recursos limitados, microserviços aumentariam complexidade operacional desnecessariamente
- **Transações ACID**: Operações financeiras requerem consistência transacional forte, mais simples em monolito
- **Desenvolvimento mais rápido**: Menos overhead de comunicação entre serviços, debugging unificado
- **Estrutura modular**: Django Apps com domain/ isolation permite futura extração para microserviços quando necessário
- **Multi-tenancy**: Row-level security é mais simples de implementar em base única

## Consequences

**Positivas**:
- Desenvolvimento e debugging mais rápidos
- Deploy simplificado com uma única aplicação
- Transações ACID nativamente suportadas
- Menos complexidade de infraestrutura
- Time-to-market acelerado

**Negativas**:
- Menor flexibilidade de escala por componente individual
- Risco de acoplamento se disciplina arquitetural não for mantida
- Single point of failure (mitigado com HA e replicação)
- Possível necessidade de refatoração futura para microserviços

## Alternatives Considered

1. **Microserviços desde o início**: Rejeitado devido à complexidade operacional excessiva para equipe pequena
2. **Monolito tradicional sem modularização**: Rejeitado por dificultar manutenibilidade e evolução
3. **SOA (Service Oriented Architecture)**: Rejeitado por ser over-engineering para o escopo atual