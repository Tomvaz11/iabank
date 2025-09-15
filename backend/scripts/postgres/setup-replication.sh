#!/bin/bash
# Setup PostgreSQL replication configuration
# IABANK DR Primary Setup

echo "Configurando replicação PostgreSQL..."

# Aguardar PostgreSQL estar pronto
sleep 5

# Adicionar entrada para replicação no pg_hba.conf
echo "host replication replicator 172.18.0.0/16 md5" >> /var/lib/postgresql/data/pg_hba.conf
echo "host replication replicator 172.19.0.0/16 md5" >> /var/lib/postgresql/data/pg_hba.conf
echo "host replication replicator 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf

# Criar diretório WAL archive
mkdir -p /var/lib/postgresql/data/pg_wal_archive
chown postgres:postgres /var/lib/postgresql/data/pg_wal_archive

# Recarregar configuração
pg_ctl reload -D /var/lib/postgresql/data

echo "Configuração de replicação concluída!"