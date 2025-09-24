# Ambiente de Testes - IABANK

## Configuração Automática da Infraestrutura

Para resolver o problema de timeout nos testes devido à falta de PostgreSQL/Redis, use os scripts de configuração automática.

### Scripts Disponíveis

#### Windows (Recomendado)
```batch
# Configurar e iniciar infraestrutura automaticamente
backend\scripts\test-setup.bat

# Executar testes (rápidos, sem coverage)
cd backend && python -m pytest tests/ --tb=short

# Executar testes com coverage (mais lento)
cd backend && python -m pytest tests/ --cov=src --cov-fail-under=85
```

#### Manual (Alternativo)
```bash
# Iniciar apenas infraestrutura
docker-compose up -d postgres redis

# Aguardar 15-20 segundos para inicialização

# Aplicar migrações
cd backend && python src/manage.py migrate

# Executar testes
python -m pytest tests/ --tb=short
```

### O que o Script Faz

1. **Verifica dependências** - Docker e Docker Compose
2. **Para containers** existentes (limpeza)
3. **Inicia infraestrutura** - PostgreSQL (porta 5433) + Redis (porta 6379)
4. **Aguarda 15 segundos** para inicialização completa
5. **Testa conectividade** - Mostra status dos serviços
6. **Aplica migrações** Django automaticamente

**Tempo total**: ~20-30 segundos

### Serviços Disponíveis

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| PostgreSQL | localhost:5433 | iabank_user / iabank_pass |
| Redis | localhost:6379 | - |
| pgAdmin | http://localhost:5050 | admin@iabank.com / admin123 |
| Redis Commander | http://localhost:8081 | - |

### Execução do Celery (Workers + Beat)

Para validar as tasks assíncronas (`T046`) utilize a infraestrutura acima (Redis obrigatório) e execute:

```bash
# Em um terminal: worker Celery
cd backend
PYTHONPATH=src celery -A config.celery worker --loglevel=info --pool=solo

# Em outro terminal: scheduler (beat)
cd backend
PYTHONPATH=src celery -A config.celery beat --loglevel=info
```

Com os processos ativos, as tarefas periódicas configuradas em `config/celery.py` serão enfileiradas automaticamente:
- `iabank.operations.tasks.update_iof_rates` (diário)
- `iabank.operations.tasks.calculate_overdue_interest` (horário)
- `iabank.finance.tasks.generate_daily_reports` (diário)

Para uma verificação rápida sem manter processos rodando, você pode inspecionar a configuração carregada:

```bash
cd backend
PYTHONPATH=src python3 -m celery -A config.celery report
```

O comando acima confirma broker/result backend, timezone e a agenda (`beat_schedule`) que inclui as tarefas adicionadas.

### Configuração Manual

Se preferir configurar manualmente:

```bash
# Iniciar apenas infraestrutura
docker-compose up -d postgres redis

# Aguardar services estarem prontos
docker-compose logs -f postgres redis

# Aplicar migrações
cd backend
python src/manage.py migrate
```

### Testes com Isolamento de Tenant

```bash
# Testes com isolamento de tenant
pytest --tenant-isolation

# Testes de contrato específicos
pytest tests/contract/test_*.py -v

# Testes com cobertura
pytest --cov=src --cov-min=85
```

### Troubleshooting

#### Timeout no PostgreSQL
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Ver logs do PostgreSQL
docker-compose logs postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

#### Timeout no Redis
```bash
# Verificar se Redis está rodando
docker-compose ps redis

# Testar conexão Redis
docker-compose exec redis redis-cli ping
```

#### Limpar Ambiente
```bash
# Parar e remover containers
docker-compose down --remove-orphans

# Remover volumes (dados)
docker-compose down -v

# Limpar tudo e recriar
docker-compose down -v && docker-compose up -d postgres redis
```

### Integração com CI/CD

O arquivo `.github/workflows/main.yml` já está configurado para usar Docker Compose nos testes:

```yaml
- name: Setup test infrastructure
  run: |
    docker-compose up -d postgres redis
    ./scripts/test-setup.sh

- name: Run tests
  run: |
    cd backend
    python -m pytest tests/ --tb=short
```

### Performance

- **PostgreSQL**: Configurado com WAL replication e checkpoints otimizados
- **Redis**: Cache persistente para acelerar testes repetidos
- **Healthchecks**: Garantem que services estejam prontos antes dos testes
- **Paralelização**: Suporte a pytest-xdist para testes paralelos

### Dados de Seed

Para testes que precisam de dados específicos:

```bash
# Criar tenant e dados básicos
python src/manage.py seed_data --tenant-id <uuid>

# Limpar dados de teste
python src/manage.py flush --verbosity=0
```

---

**Nota**: Esta configuração resolve o problema de timeout identificado na análise, automatizando o levante da infraestrutura local antes da execução dos testes.
