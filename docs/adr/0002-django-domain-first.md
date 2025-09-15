# 0002. Arquitetura Django-Domain-First

**Status**: Accepted
**Date**: 2025-09-12
**Authors**: Equipe IABANK

## Context

Precisávamos definir a estrutura interna dos Django Apps para garantir separação clara entre lógica de negócio e infraestrutura, especialmente importante em um sistema financeiro onde as regras de negócio são complexas e críticas.

## Decision

Implementar arquitetura Django-Domain-First com isolamento estrito da camada de domínio dentro de cada Django App.

## Rationale

- **Separação clara**: Domain layer isolado não pode importar Django, garantindo lógica de negócio pura
- **Testabilidade**: Domain services podem ser testados independentemente de Django/ORM
- **Manutenibilidade**: Lógica de negócio centralizada e independente de framework
- **Evolução**: Facilita migração futura para outros frameworks se necessário
- **Complexidade financeira**: Cálculos de IOF, CET e regras bancárias requerem isolamento rigoroso

## Consequences

**Positivas**:
- Lógica de negócio testável independentemente
- Menor acoplamento com Django framework
- Facilita reutilização de código entre diferentes contextos
- Melhora a clareza da separação de responsabilidades
- Suporte a TDD mais efetivo

**Negativas**:
- Maior complexidade estrutural inicial
- Curva de aprendizado para desenvolvedores acostumados com Django tradicional
- Overhead de mapeamento entre domain entities e Django models
- Requer disciplina arquitetural constante

## Alternatives Considered

1. **Django tradicional "fat models"**: Rejeitado por misturar lógica de negócio com infraestrutura
2. **Clean Architecture completa**: Rejeitado por ser over-engineering, Django-Domain-First é mais pragmático
3. **Hexagonal Architecture**: Considerado, mas Django-Domain-First oferece melhor balance para o contexto

## Implementation Details

Estrutura obrigatória em cada Django App:

```
app_name/
├── domain/
│   ├── entities.py      # Pydantic models (pure business logic)
│   └── services.py      # Business rules and calculations
├── models.py           # Django ORM models (infrastructure)
├── views.py            # DRF endpoints (infrastructure)
└── serializers.py      # Request/Response formatting
```

**Regra crítica**: `domain/` não pode importar Django.