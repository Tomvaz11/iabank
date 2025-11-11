#!/usr/bin/env bash
set -euo pipefail

# Verifica se o corpo do PR aparenta usar o template (marca "## Checklist" ou frase da checklist).
# Entrada via env: PR_BODY (opcional), PR_NUMBER, REPO, GH_TOKEN, API_URL, GITHUB_EVENT_PATH

marker_regex='(^|\n)##[[:space:]]*Checklist|inclui[[:space:]]+pelo[[:space:]]+menos[[:space:]]+uma[[:space:]]+tag[[:space:]]+@SC-00x'

source_used="event"
body="${PR_BODY:-}"

# Preferir sempre buscar o PR atualizado via API; fazer fallback para evento somente se falhar.
if command -v gh >/dev/null 2>&1 && [ -n "${PR_NUMBER:-}" ] && [ -n "${REPO:-}" ]; then
  if pr_json=$(gh api -H "Accept: application/vnd.github+json" "repos/$REPO/pulls/$PR_NUMBER" 2>/dev/null); then
    latest_body=$(printf '%s' "$pr_json" | jq -r '(.body // "")')
    if [ -n "$latest_body" ]; then
      body="$latest_body"
      source_used="api-gh"
    fi
  fi
fi

if [ "$source_used" = "event" ]; then
  if command -v curl >/dev/null 2>&1 && [ -n "${PR_NUMBER:-}" ] && [ -n "${REPO:-}" ] && [ -n "${GH_TOKEN:-}" ] && [ -n "${API_URL:-}" ]; then
    if pr_json=$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" "$API_URL/repos/$REPO/pulls/$PR_NUMBER" 2>/dev/null); then
      latest_body=$(printf '%s' "$pr_json" | jq -r '(.body // "")')
      if [ -n "$latest_body" ]; then
        body="$latest_body"
        source_used="api-curl"
      fi
    fi
  fi
fi

if [ "$source_used" = "event" ] && [ -z "$body" ] && [ -n "${GITHUB_EVENT_PATH:-}" ] && [ -f "$GITHUB_EVENT_PATH" ]; then
  body=$(jq -r '(.pull_request.body // "")' "$GITHUB_EVENT_PATH" || echo "")
  source_used="event-file"
fi

if printf '%s' "$body" | tr '\r' '\n' | grep -Eiq "$marker_regex"; then
  echo "Template de PR aparente detectado (fonte: $source_used)"
else
  echo "::error::Utilize o template de PR (inclua a seção \"## Checklist\")." \
       "O template reduz falhas no gate @SC-00x."
  echo "Fonte de dados utilizada: $source_used"
  echo "Corpo (até 120 chars): $(printf '%s' "$body" | tr '\n' ' ' | head -c 120)"
  exit 1
fi
