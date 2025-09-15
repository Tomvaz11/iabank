# 0003. Multi-tenancy Row-Level Security

**Status**: Accepted
**Date**: 2025-09-12
**Authors**: Equipe IABANK

## Context

IABANK é uma plataforma SaaS que atende múltiplas empresas de crédito simultaneamente. Cada tenant (empresa) deve ter isolamento absoluto dos seus dados, sem possibilidade de vazamento entre tenants. A decisão de arquitetura de multi-tenancy é crítica para segurança e compliance.

## Decision

Implementar multi-tenancy usando Row-Level Security (RLS) com tenant_id obrigatório em todos os modelos e filtro automático via middleware.

## Rationale

- **Segurança máxima**: Isolamento garantido no nível do banco de dados
- **Performance**: Melhor que schema-per-tenant ou database-per-tenant para muitos tenants pequenos
- **Manutenibilidade**: Migrations unificadas, estrutura única
- **Compliance**: Auditoria centralizada facilita conformidade LGPD
- **Cost-effective**: Recursos compartilhados otimizam custos de infraestrutura

## Consequences

**Positivas**:
- Isolamento de dados garantido no nível do PostgreSQL
- Estrutura de código simplificada (um só schema)
- Performance otimizada com índices compostos
- Backup e recovery unificados
- Facilita analytics cross-tenant (quando autorizado)

**Negativas**:
- Risco de bugs de implementação comprometendo isolamento
- Queries sempre incluem tenant_id (overhead mínimo)
- Complexidade adicional em testes e debugging
- Migração para outras estratégias mais complexa

## Alternatives Considered

1. **Database-per-tenant**: Rejeitado por complexidade operacional e custos de infraestrutura
2. **Schema-per-tenant**: Rejeitado por limites do PostgreSQL e complexidade de migrations
3. **Application-level filtering**: Considerado insuficiente para segurança financeira

## Implementation Details

### Arquitetura Obrigatória

1. **BaseTenantModel**: Todos os modelos herdam e incluem tenant_id obrigatório
2. **TenantMiddleware**: Filtro automático por tenant_id em todas as queries
3. **Índices compostos**: tenant_id sempre como primeira coluna
4. **CLI commands**: Sempre requerem --tenant-id explícito

### Medidas de Segurança

- Middleware valida tenant_id em cada request
- Testes automatizados de isolamento para cada endpoint
- Factory-boy com propagação automática de tenant_id
- Auditoria completa via django-simple-history com tenant context

### PostgreSQL Row-Level Security

```sql
-- Exemplo de política RLS (futura implementação)
ALTER TABLE app_model ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON app_model
    FOR ALL TO app_role
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```