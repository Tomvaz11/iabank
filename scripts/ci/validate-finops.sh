#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODEL_PATH="${MODEL_PATH:-$ROOT_DIR/configs/finops/seed-data.cost-model.yaml}"
SCHEMA_PATH="${SCHEMA_PATH:-$ROOT_DIR/contracts/finops/seed-data.cost-model.schema.json}"

if [ ! -f "$MODEL_PATH" ]; then
  echo "[finops] Arquivo de modelo nao encontrado: $MODEL_PATH" >&2
  exit 1
fi

if [ ! -f "$SCHEMA_PATH" ]; then
  echo "[finops] Schema nao encontrado: $SCHEMA_PATH" >&2
  exit 1
fi

python3 - "$MODEL_PATH" "$SCHEMA_PATH" <<'PY'
import json
import sys
from pathlib import Path

model_path = Path(sys.argv[1])
schema_path = Path(sys.argv[2])

errors: list[str] = []

try:
    model = json.loads(model_path.read_text())
except json.JSONDecodeError as exc:
    sys.exit(f"[finops] Arquivo invalido ({model_path}): {exc}")

schema = json.loads(schema_path.read_text())

required_keys = schema["required"]
for key in required_keys:
    if key not in model:
        errors.append(f"campo obrigatorio ausente: {key}")

if model.get("schema_version") != "v1":
    errors.append("schema_version deve ser v1")

if model.get("currency") != "BRL":
    errors.append("currency deve ser BRL")

worm_cfg = model.get("worm", {})
min_days = schema["properties"]["worm"]["properties"]["minimum_retention_days"]["minimum"]
retention_days = worm_cfg.get("minimum_retention_days", 0)
if retention_days < min_days:
    errors.append(f"retencao WORM abaixo do minimo ({retention_days}d < {min_days}d)")

environments = model.get("environments", {})
allowed_envs = set(environments.keys())
for env in worm_cfg.get("required_environments", []):
    if env not in allowed_envs:
        errors.append(f"worm.required_environments contem ambiente nao declarado: {env}")

for env_name, env_cfg in environments.items():
    cap = env_cfg.get("cost_cap_brl")
    error_budget = env_cfg.get("error_budget_pct")
    rate_limit = env_cfg.get("rate_limit_rpm")
    slo = env_cfg.get("slo", {})
    for field, value in [("cost_cap_brl", cap), ("error_budget_pct", error_budget), ("rate_limit_rpm", rate_limit)]:
        if value is None:
            errors.append(f"{env_name}.{field} ausente")
    if isinstance(cap, (int, float)) and cap < 0:
        errors.append(f"{env_name}.cost_cap_brl deve ser >=0")
    if isinstance(error_budget, (int, float)) and (error_budget < 0 or error_budget > 100):
        errors.append(f"{env_name}.error_budget_pct deve estar entre 0 e 100")
    if isinstance(rate_limit, int) and rate_limit <= 0:
        errors.append(f"{env_name}.rate_limit_rpm deve ser positivo")

    if env_name in {"dev", "homolog"} and isinstance(cap, (int, float)) and cap > 25:
        errors.append(f"{env_name}.cost_cap_brl acima do teto permitido (25)")
    if env_name in {"staging", "perf"} and isinstance(cap, (int, float)) and cap > 125:
        errors.append(f"{env_name}.cost_cap_brl acima do teto permitido (125)")

    if slo:
        for field in ("p95_ms", "p99_ms"):
            val = slo.get(field)
            if val is None or val <= 0:
                errors.append(f"{env_name}.slo.{field} deve ser inteiro positivo")
        if slo.get("throughput_rps") is not None and slo["throughput_rps"] <= 0:
            errors.append(f"{env_name}.slo.throughput_rps deve ser positivo")

modes = model.get("modes", {})
for mode in ("baseline", "carga", "dr"):
    if mode not in modes:
        errors.append(f"modo obrigatorio ausente: {mode}")
        continue
    cfg = modes[mode]
    runtime = cfg.get("max_runtime_minutes")
    if runtime is None or runtime <= 0:
        errors.append(f"{mode}.max_runtime_minutes deve ser positivo")
    budget_alert = cfg.get("budget_alert_pct")
    if budget_alert is None or budget_alert <= 0 or budget_alert > 100:
        errors.append(f"{mode}.budget_alert_pct deve estar entre 0 e 100")

components = model.get("components", {})
for key in schema["properties"]["components"]["required"]:
    value = components.get(key)
    if value is None:
        errors.append(f"components.{key} ausente")
    elif value < 0:
        errors.append(f"components.{key} deve ser >= 0")

dataset_caps = model.get("dataset_caps", {})
for key in ("baseline_multiplier", "carga_multiplier", "dr_multiplier"):
    if dataset_caps.get(key) is None:
        errors.append(f"dataset_caps.{key} ausente")
    elif dataset_caps[key] < 1:
        errors.append(f"dataset_caps.{key} deve ser >= 1")

if errors:
    print("[finops] Falhas na validacao:")
    for err in errors:
        print(f"- {err}")
    sys.exit(1)

print(f"[finops] OK: {model_path.name} validado contra {schema_path.name}")
PY
