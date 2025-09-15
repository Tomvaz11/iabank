-- Inicialização do PostgreSQL Primary para Disaster Recovery
-- IABANK DR Primary Database Setup

-- Criar usuário de replicação
CREATE USER replicator WITH REPLICATION PASSWORD 'repl_password';

-- Configurar permissões para replicação
GRANT CONNECT ON DATABASE iabank TO replicator;

-- Adicionar entrada no pg_hba.conf para replicação
-- Isso será feito via script shell pois SQL não pode modificar pg_hba.conf

-- Verificar configurações de replicação
SELECT name, setting FROM pg_settings WHERE name IN (
    'wal_level',
    'max_wal_senders',
    'wal_keep_size',
    'hot_standby',
    'archive_mode'
);

-- Verificar usuários de replicação
SELECT usename, userepl FROM pg_user WHERE userepl = true;