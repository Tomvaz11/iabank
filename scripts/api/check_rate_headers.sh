#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'USAGE'
Usage: check_rate_headers.sh [-f <headers_file>] [-u <url>] [--expect-429]

Validates presence of RateLimit headers (RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset)
 and Retry-After (when HTTP status is 429) in HTTP response headers.

Options:
  -f <headers_file>   File containing raw HTTP response headers (e.g. output of curl -I)
  -u <url>            Perform a HEAD request against the given URL (requires curl)
  --expect-429        Fail if the response does not include a 429 status line
  -h, --help          Show this help message

If neither -f nor -u are provided, the script reads headers from STDIN.
The script exits with status 0 when all required headers are present.
USAGE
}

expect_429=false
headers_source="stdin"
headers_content=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f)
      headers_source="file"
      headers_file="$2"
      shift 2
      ;;
    -u)
      headers_source="url"
      target_url="$2"
      shift 2
      ;;
    --expect-429)
      expect_429=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      show_help >&2
      exit 1
      ;;
  esac
done

capture_headers() {
  case "$headers_source" in
    file)
      if [[ ! -f "$headers_file" ]]; then
        echo "ERROR: Header file '$headers_file' not found" >&2
        exit 1
      fi
      headers_content=$(tr -d '\r' < "$headers_file")
      ;;
    url)
      if ! command -v curl >/dev/null 2>&1; then
        echo "ERROR: curl not available to fetch $target_url" >&2
        exit 1
      fi
      headers_content=$(curl -sS -I "$target_url" | tr -d '\r')
      ;;
    stdin)
      headers_content=$(tr -d '\r')
      ;;
  esac
}

if [[ "$headers_source" == "stdin" ]]; then
  capture_headers <<<"$(cat)"
else
  capture_headers
fi

if [[ -z "$headers_content" ]]; then
  echo "ERROR: no headers to inspect" >&2
  exit 1
fi

status_line=$(printf '%s\n' "$headers_content" | head -n1)
if $expect_429 && [[ "$status_line" != *" 429"* ]]; then
  echo "ERROR: expected a 429 response but got: $status_line" >&2
  exit 1
fi

missing=()
for header in "RateLimit-Limit" "RateLimit-Remaining" "RateLimit-Reset"; do
  if ! printf '%s\n' "$headers_content" | grep -qi "^$header:"; then
    missing+=("$header")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ERROR: missing header(s): ${missing[*]}" >&2
  exit 1
fi

if printf '%s\n' "$headers_content" | grep -qi " 429"; then
  if ! printf '%s\n' "$headers_content" | grep -qi '^Retry-After:'; then
    echo "ERROR: 429 response detected but Retry-After header is absent" >&2
    exit 1
  fi
fi

echo "✓ Rate limiting headers verified"
exit 0
