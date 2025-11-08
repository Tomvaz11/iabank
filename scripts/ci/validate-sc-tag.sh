#!/usr/bin/env bash
set -euo pipefail

# Entrada via env:
# - PR_TITLE, PR_BODY (opcional, do contexto do evento)
# - PR_NUMBER, REPO, GH_TOKEN, API_URL (para fallback API)
# - REQUIRED_TAG_REGEX (regex da tag), default '@SC-00[1-5]'
# - GITHUB_EVENT_PATH (fallback final)

REQUIRED_TAG_REGEX="${REQUIRED_TAG_REGEX:-@SC-00[1-5]}"

source_used="event"
title="${PR_TITLE:-}"
body="${PR_BODY:-}"

# Fallback: API via gh
if [ -z "$title" ] || [ -z "$body" ]; then
  if command -v gh >/dev/null 2>&1 && [ -n "${PR_NUMBER:-}" ] && [ -n "${REPO:-}" ]; then
    if pr_json=$(gh api -H "Accept: application/vnd.github+json" "repos/$REPO/pulls/$PR_NUMBER" 2>/dev/null); then
      title=$(printf '%s' "$pr_json" | jq -r '(.title // "")')
      body=$(printf '%s' "$pr_json" | jq -r '(.body // "")')
      source_used="api-gh"
    fi
  fi
fi

# Fallback alternativo: API via curl
if [ -z "$title" ] || [ -z "$body" ]; then
  if command -v curl >/dev/null 2>&1 && [ -n "${PR_NUMBER:-}" ] && [ -n "${REPO:-}" ] && [ -n "${GH_TOKEN:-}" ] && [ -n "${API_URL:-}" ]; then
    if pr_json=$(curl -fsSL -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" "$API_URL/repos/$REPO/pulls/$PR_NUMBER" 2>/dev/null); then
      title=$(printf '%s' "$pr_json" | jq -r '(.title // "")')
      body=$(printf '%s' "$pr_json" | jq -r '(.body // "")')
      source_used="api-curl"
    fi
  fi
fi

# Fallback final: arquivo de evento
if [ -z "$title" ] && [ -z "$body" ] && [ -n "${GITHUB_EVENT_PATH:-}" ] && [ -f "$GITHUB_EVENT_PATH" ]; then
  title=$(jq -r '(.pull_request.title // "")' "$GITHUB_EVENT_PATH" || echo "")
  body=$(jq -r '(.pull_request.body // "")' "$GITHUB_EVENT_PATH" || echo "")
  source_used="event-file"
fi

found_title=0
found_body=0
if printf '%s' "$title" | grep -Eq "${REQUIRED_TAG_REGEX}"; then
  found_title=1
fi
if printf '%s' "$body" | grep -Eq "${REQUIRED_TAG_REGEX}"; then
  found_body=1
fi

if [ "$found_title" -eq 0 ] && [ "$found_body" -eq 0 ]; then
  echo "::error::PR precisa mencionar pelo menos uma tag @SC-00x (SC-001..SC-005)."
  echo "Fonte de dados utilizada: $source_used"
  echo "Presença da tag: título=$found_title, corpo=$found_body"
  echo "Título (até 120 chars): $(printf '%s' "$title" | head -c 120)"
  echo "Corpo (até 120 chars, normalizado): $(printf '%s' "$body" | tr '\n' ' ' | head -c 120)"
  exit 1
else
  echo "Tag @SC-00x detectada (fonte: $source_used)"
  if [ "$found_title" -eq 1 ]; then echo " - Encontrada no título"; fi
  if [ "$found_body" -eq 1 ]; then echo " - Encontrada no corpo"; fi
fi

