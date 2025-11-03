#!/usr/bin/env bash

# Script auxiliar para exportar variáveis necessárias na stack foundation.
# Use com: source scripts/dev/foundation-env.sh

export FOUNDATION_DB_VENDOR="${FOUNDATION_DB_VENDOR:-postgresql}"
export FOUNDATION_DB_HOST="${FOUNDATION_DB_HOST:-127.0.0.1}"
export FOUNDATION_DB_PORT="${FOUNDATION_DB_PORT:-5432}"
export FOUNDATION_DB_NAME="${FOUNDATION_DB_NAME:-foundation}"
export FOUNDATION_DB_USER="${FOUNDATION_DB_USER:-foundation}"
export FOUNDATION_DB_PASSWORD="${FOUNDATION_DB_PASSWORD:-foundation}"
export FOUNDATION_DB_CONN_MAX_AGE="${FOUNDATION_DB_CONN_MAX_AGE:-60}"
export FOUNDATION_PGCRYPTO_KEY="${FOUNDATION_PGCRYPTO_KEY:-dev-only-pgcrypto-key}"

export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
export OTEL_SERVICE_NAME="${OTEL_SERVICE_NAME:-foundation-frontend-cli}"
export OTEL_RESOURCE_ATTRIBUTES="${OTEL_RESOURCE_ATTRIBUTES:-deployment.environment=local,service.namespace=iabank}"

echo "Variáveis FOUNDATION_* e OTEL_* exportadas para o shell atual."
