# IABANK DR Testing Procedure
**T086 DR Pilot Light - Comprehensive Testing Documentation**

---

## 📋 Overview

Esta documentação estabelece procedimentos detalhados para testes de Disaster Recovery (DR) do sistema IABANK, conforme implementação T086 DR Pilot Light.

**Objetivos:**
- Validar capacidade de recuperação em caso de falha regional
- Verificar atendimento aos targets RTO (<4h) e RPO (<5min)
- Manter equipe treinada em procedimentos de emergência
- Identificar e corrigir pontos de falha

---

## 🗓️ Cronograma de Testes

### Teste Completo (Trimestral)
**Frequência:** A cada 3 meses
**Duração:** 4-6 horas
**Janela:** Domingo às 02:00-08:00 BRT
**Próximos:** Jan 15, Abr 15, Jul 15, Out 15

### Teste Parcial (Mensal)
**Frequência:** Todo primeiro domingo do mês
**Duração:** 1-2 horas
**Foco:** Health checks, conectividade, monitoramento

### Teste de Emergência (Ad-hoc)
**Trigger:** Incidentes reais, mudanças críticas
**Aprovação:** CTO + DevOps Lead

---

## ✅ Checklist Pré-Teste (48h antes)

### Preparação Técnica
- [ ] **Backup PITR verificado** - Confirmar backups funcionais últimas 24h
- [ ] **Replicação ativa** - Validar lag < 5min entre primary e replica
- [ ] **Ambiente DR limpo** - Verificar recursos DR não estão em uso
- [ ] **Scripts atualizados** - Validar versão mais recente do failover.sh
- [ ] **Terraform validado** - `terraform plan` sem erros
- [ ] **Credenciais AWS** - Verificar acesso às duas regiões (us-east-1, us-west-2)
- [ ] **DNS propagado** - Confirmar registros Route53 corretos

### Comunicação e Coordenação
- [ ] **Equipe notificada** - DevOps, SRE, Produto, C-Level
- [ ] **Cliente comunicado** - Email 48h + 2h antes (se necessário)
- [ ] **War room preparada** - Slack #dr-testing, Zoom room
- [ ] **Runbook disponível** - Links e procedimentos acessíveis
- [ ] **Monitoramento configurado** - Dashboards DR prontos

### Checklist 24h Antes
- [ ] **Reconfirmar janela** - Sem conflitos ou eventos críticos
- [ ] **Baseline capturado** - Métricas performance normal
- [ ] **Equipe confirmada** - Disponibilidade dos responsáveis
- [ ] **Plano rollback** - Procedimento retorno ao normal

### Checklist 2h Antes
- [ ] **Status final** - Todos os sistemas operacionais
- [ ] **Logs limpos** - Verificar ausência de alertas críticos
- [ ] **Time online** - Todos os participantes conectados
- [ ] **Go/No-Go** - Decisão final para prosseguir

---

## 🚨 Procedimento de Teste Completo

### Fase 1: Simulação de Falha (15min)
```bash
# 1. Simular falha da região primária
# ATENÇÃO: Não execute em produção real!

# 1.1 Parar aplicação primária (simulação)
echo "Simulando falha da aplicação primária..."
# docker-compose down (ambiente de staging)

# 1.2 Marcar primary DB como indisponível (simulação)
# aws rds stop-db-instance --db-instance-identifier iabank-primary

# 1.3 Iniciar cronômetro RTO
DR_START_TIME=$(date +%s)
echo "DR Test iniciado: $(date)"
```

### Fase 2: Execução do Failover (60-90min)
```bash
# 2.1 Executar script de failover
cd backend/scripts/backup
./failover.sh --force

# 2.2 Monitorar progresso
tail -f /tmp/iabank_failover_*.log

# 2.3 Verificar promoção do replica
aws rds describe-db-instances \
  --db-instance-identifier iabank-dr-replica \
  --region us-west-2 \
  --query 'DBInstances[0].DBInstanceStatus'
```

### Fase 3: Verificação Funcional (30-45min)
```bash
# 3.1 Health checks básicos
curl -f https://api.iabank.com/health/
curl -f https://api.iabank.com/api/v1/auth/status/

# 3.2 Conectividade database
psql -h <DR_ENDPOINT> -U iabank -d iabank -c "SELECT NOW();"

# 3.3 Verificar dados replicados
psql -h <DR_ENDPOINT> -U iabank -d iabank -c "SELECT COUNT(*) FROM django_migrations;"
```

### Fase 4: Testes Funcionais Críticos (45-60min)

#### Teste 1: Autenticação e Autorização
- [ ] **Login usuário admin** - JWT token válido
- [ ] **Login usuário consultor** - Permissões corretas
- [ ] **MFA funcionando** - TOTP/SMS operacional
- [ ] **Logout seguro** - Token invalidado

#### Teste 2: Operações de Negócio
- [ ] **Criar cliente** - CRUD clientes funcionando
- [ ] **Simulação empréstimo** - Cálculos IOF/CET corretos
- [ ] **Aprovar empréstimo** - Workflow completo
- [ ] **Registrar pagamento** - Atualização parcelas

#### Teste 3: Relatórios e Consultas
- [ ] **Dashboard financeiro** - Dados corretos e atualizados
- [ ] **Relatório mensal** - Geração sem erros
- [ ] **Export Excel** - Download funcional
- [ ] **Auditoria logs** - Trilha preservada

### Fase 5: Performance e Monitoramento (30min)
```bash
# 5.1 Latência API
curl -w "@scripts/dr/curl-format.txt" -o /dev/null -s https://api.iabank.com/health/

# 5.2 Throughput database
pgbench -h <DR_ENDPOINT> -U iabank -d iabank -T 60 -c 5

# 5.3 Verificar métricas
# - Response time < 500ms
# - CPU < 70%
# - Memory < 80%
# - Disk I/O normal
```

---

## 🔄 Procedimento de Rollback

### Quando Executar Rollback
- Testes falham nos critérios mínimos
- RTO excede 6 horas (limite crítico)
- Inconsistências de dados detectadas
- Degradação severa de performance

### Passos de Rollback
```bash
# 1. Parar aplicação DR
kubectl scale deployment iabank-api --replicas=0 -n dr

# 2. Restaurar aplicação primária
kubectl scale deployment iabank-api --replicas=3 -n primary

# 3. Atualizar DNS (se necessário)
# Route53 deve fazer automaticamente via health checks

# 4. Verificar restauração
curl -f https://api.iabank.com/health/
```

---

## 📊 Métricas e KPIs

### Targets Obrigatórios
| Métrica | Target | Crítico |
|---------|---------|---------|
| **RTO** | < 4 horas | < 6 horas |
| **RPO** | < 5 minutos | < 15 minutos |
| **Disponibilidade** | 99.9% | 99.5% |
| **Latência API** | < 500ms | < 1000ms |
| **Perda de dados** | 0% | < 0.001% |

### Medições Durante Teste
```bash
# RTO Calculation
DR_END_TIME=$(date +%s)
RTO_SECONDS=$((DR_END_TIME - DR_START_TIME))
RTO_MINUTES=$((RTO_SECONDS / 60))
echo "RTO Achieved: ${RTO_MINUTES} minutes"

# RPO Verification
# Comparar último timestamp primary vs DR
```

---

## 📝 Template de Relatório

### Informações Básicas
- **Data/Hora:** [YYYY-MM-DD HH:MM]
- **Tipo de Teste:** [Completo/Parcial/Emergência]
- **Duração:** [HH:MM]
- **Participantes:** [Nome, Função]

### Resultados Técnicos
- **RTO Alcançado:** [HH:MM]
- **RPO Verificado:** [MM:SS]
- **Sistemas Testados:** [Lista]
- **Falhas Encontradas:** [Descrição]

### Funcionalidades Validadas
- [ ] Autenticação/Autorização
- [ ] Operações Críticas de Negócio
- [ ] Relatórios e Consultas
- [ ] Performance e Monitoramento

### Issues Identificados
| Severidade | Descrição | Responsável | Prazo |
|------------|-----------|-------------|-------|
| Alta | [Descrição] | [Nome] | [Data] |
| Média | [Descrição] | [Nome] | [Data] |

### Ações de Follow-up
1. [Ação] - [Responsável] - [Prazo]
2. [Ação] - [Responsável] - [Prazo]

### Recomendações
- **Melhorias de Processo:** [Lista]
- **Atualizações Técnicas:** [Lista]
- **Treinamento Necessário:** [Lista]

---

## 🚨 Contatos de Emergência

### Equipe Principal
- **DevOps Lead:** [Nome] - [Telefone] - [Email]
- **SRE Principal:** [Nome] - [Telefone] - [Email]
- **DBA:** [Nome] - [Telefone] - [Email]
- **CTO:** [Nome] - [Telefone] - [Email]

### Fornecedores Críticos
- **AWS Support:** [Case ID] - [Telefone]
- **CloudFlare:** [Account ID] - [Portal]
- **PagerDuty:** [Integration Key]

### Comunicação
- **Slack DR:** #dr-testing, #incidents
- **War Room:** [Zoom/Teams Link]
- **Status Page:** [URL interno/externo]

---

## 📚 Referências e Links

### Documentação Técnica
- [Arquitetura DR](../architecture/dr-design.md)
- [Runbook Operacional](../operations/runbook.md)
- [Scripts de Automação](../../backend/scripts/backup/)

### Dashboards e Monitoramento
- [Dashboard DR](https://grafana.iabank.com/d/dr-monitoring)
- [AWS CloudWatch](https://console.aws.amazon.com/cloudwatch/)
- [Route53 Health Checks](https://console.aws.amazon.com/route53/healthchecks/)

### Procedimentos Relacionados
- [Backup e Restauração](backup-procedures.md)
- [Incident Response](incident-response.md)
- [Change Management](change-management.md)

---

**Última Atualização:** 2025-09-15
**Próxima Revisão:** 2025-12-15
**Versão:** 1.0 (T086 DR Pilot Light)
**Aprovado por:** DevOps Team