# Runbook: Resposta a Incidentes de Observabilidade/SLO

## Objetivo
Descrever o fluxo padrão de resposta quando métricas DORA/SLO ultrapassarem limites ou quando alertas críticos forem disparados.

## Passo a Passo
1. **Detecção**
   - Confirmar alerta no PagerDuty/Slack.
   - Registrar horário de detecção e responsável.
2. **Triagem**
   - Verificar dashboards prioritários (latência, taxa de erro, saturação).
   - Validar se o alerta é real ou falso positivo.
3. **Mitigação Inicial**
   - Aplicar ações imediatas (rollback, feature flag, scale-out).
   - Notificar stakeholders principais.
4. **Investigação**
   - Correlacionar logs/traces de acordo com o span ou request_id afetado.
   - Executar o script `python scripts/observability/check_structlog.py <log>` se houver suspeita de vazamento de PII.
5. **Resolução**
   - Confirmar retorno ao estado normal via dashboards.
   - Atualizar o status do alerta para resolvido.
6. **Pós-Incidente**
   - Abrir `docs/runbooks/incident-report.md` e documentar o ocorrido.
   - Agendar retrospectiva e definir ações preventivas.

## Contatos
- **Time de SRE**: sre@iabank.example
- **Segurança**: security@iabank.example
- **Gestão de Produto**: produto@iabank.example

## Ferramentas Úteis
- Grafana dashboards (`SLO Core`, `API Resilience`)
- Sentry Issues Linkado ao serviço afetado
- CLI `vault` para revogação de credenciais

> Sempre após o incidente, avalie se há necessidade de atualizar a constituição, ADRs ou scripts de automação.
