# Setup PostgreSQL para IABANK

Este guia explica como configurar o PostgreSQL com Docker para desenvolvimento da aplicação IABANK multi-tenant.

## Pré-requisitos

- Docker Desktop instalado e rodando
- Python 3.11+ e ambiente virtual configurado

## 1. Iniciar PostgreSQL com Docker

```bash
# No diretório raiz do projeto
docker-compose up -d postgres redis
```

Isso irá:
- Criar um container PostgreSQL na porta 5433
- Criar um container Redis na porta 6379
- Inicializar extensões PostgreSQL necessárias
- Configurar volumes persistentes para dados

### Serviços Disponíveis

- **PostgreSQL**: `localhost:5433`
  - Database: `iabank`
  - User: `postgres`
  - Password: `postgres`

- **Redis**: `localhost:6379`

- **pgAdmin** (interface web): `http://localhost:5050`
  - Email: `admin@iabank.local`
  - Password: `admin123`

- **Redis Commander**: `http://localhost:8081`

## 2. Configurar Django

### 2.1 Ativar Ambiente Virtual

```bash
cd backend
# Windows
./venv/Scripts/activate.bat

# Linux/Mac
source venv/bin/activate
```

### 2.2 Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2.3 Configurar Variáveis de Ambiente

O arquivo `.env` já foi criado com as configurações corretas:

```env
DB_NAME=iabank
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5433
```

## 3. Executar Migrações

```bash
# Aplicar migrações
python src/manage.py migrate

# Aplicar migrações específicas do core
python src/manage.py migrate core
```

## 4. Criar Tenant de Desenvolvimento

```bash
# Criar tenant com ID específico
python src/manage.py setup_dev_tenant --tenant-id 00000000-0000-0000-0000-000000000001

# Ou criar tenant com dados customizados
python src/manage.py setup_dev_tenant \
  --name "Minha Empresa" \
  --slug "minha-empresa" \
  --cnpj "12.345.678/0001-90" \
  --email "admin@minhaempresa.com"
```

O comando irá exibir:
- ID do tenant criado
- Configurações para adicionar ao `.env`
- Header para usar nas requisições API

## 5. Testar Multi-tenancy

### 5.1 Verificar Middleware

O middleware `TenantMiddleware` já está configurado e irá:
- Extrair tenant ID de headers HTTP (`X-Tenant-ID`)
- Validar se o tenant existe e está ativo
- Filtrar automaticamente queries por tenant

### 5.2 Testar com Django Shell

```bash
python src/manage.py shell
```

```python
from iabank.core.models import Tenant

# Listar todos os tenants
tenants = Tenant.objects.all()
print(f"Total de tenants: {tenants.count()}")

for tenant in tenants:
    print(f"- {tenant.name} ({tenant.id})")
```

## 6. Comandos Úteis

### Parar Containers

```bash
docker-compose down
```

### Reiniciar com Dados Limpos

```bash
docker-compose down -v  # Remove volumes
docker-compose up -d postgres redis
```

### Verificar Logs

```bash
docker-compose logs postgres
docker-compose logs redis
```

### Backup do Banco

```bash
docker exec iabank_postgres pg_dump -U postgres iabank > backup.sql
```

### Restaurar Backup

```bash
docker exec -i iabank_postgres psql -U postgres iabank < backup.sql
```

## 7. Solução de Problemas

### Container PostgreSQL não inicia

```bash
# Verificar se a porta 5433 está em uso
netstat -an | grep :5433

# Verificar logs do container
docker-compose logs postgres
```

### Erro de conexão Django → PostgreSQL

1. Verificar se o container está rodando:
   ```bash
   docker-compose ps
   ```

2. Testar conexão manual:
   ```bash
   docker exec -it iabank_postgres psql -U postgres iabank
   ```

3. Verificar configurações em `.env`:
   - `DB_HOST=localhost`
   - `DB_PORT=5433`
   - `DB_NAME=iabank`

### Problemas com Multi-tenancy

1. Verificar se o middleware está configurado em `settings/base.py`
2. Confirmar se o tenant existe:
   ```bash
   python src/manage.py shell -c "from iabank.core.models import Tenant; print(Tenant.objects.count())"
   ```

3. Testar com header HTTP:
   ```bash
   curl -H "X-Tenant-ID: seu-tenant-id" http://localhost:8000/api/health/
   ```

## 8. Próximos Passos

Após configurar o PostgreSQL:

1. **T006**: Implementar autenticação JWT com claims de tenant
2. **T007**: Criar factory classes para testes com tenant automático
3. **T008**: Implementar modelos de domínio (Customer, Loan, etc.)
4. **T009**: Criar contract tests para endpoints multi-tenant

---

**Configuração completada com sucesso!** 🎉

O T005 (Setup PostgreSQL com Docker e configurações multi-tenant) foi implementado com:
- ✅ Docker Compose com PostgreSQL, Redis, pgAdmin
- ✅ Modelos base Tenant e BaseTenantModel
- ✅ Middleware de multi-tenancy automático
- ✅ **Row-Level Security (RLS) completo**
- ✅ **PITR com arquivamento WAL contínuo (FR-109)**
- ✅ **Sistema de backup e retenção (FR-111)**
- ✅ Sistema de migração e comandos de setup
- ✅ Documentação completa de uso

## Funcionalidades de Segurança e Backup

### Row-Level Security (RLS)
```bash
# Ativar RLS em todas as tabelas multi-tenant
python src/manage.py enable_rls

# Verificar status RLS
python src/manage.py enable_rls --dry-run
```

### Point-in-Time Recovery (PITR)
```bash
# Verificar configuração PITR
python src/manage.py manage_backups status

# Criar backup base para PITR
python src/manage.py manage_backups backup

# Restaurar para ponto específico no tempo
python src/manage.py manage_backups restore --pitr-time "2024-01-15 14:30:00"
```

### Gestão de Backups (FR-111)
```bash
# Listar backups disponíveis
python src/manage.py manage_backups list

# Executar limpeza de backups (retenção 30 dias)
python src/manage.py manage_backups cleanup

# Executar scripts de backup manualmente
./backend/scripts/backup/backup_database.sh
./backend/scripts/backup/restore_database.sh --help
```

### Configurações PITR no PostgreSQL
- **wal_level**: replica
- **archive_mode**: on
- **wal_keep_size**: 1GB
- **checkpoint_completion_target**: 0.9
- **Retenção WAL**: 14 dias (FR-111)
- **Retenção backups**: 30 dias (FR-111)