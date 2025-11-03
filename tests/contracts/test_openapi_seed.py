from pathlib import Path

import yaml


FEATURE_SPEC = Path("specs/002-f-10-fundacao/contracts/frontend-foundation.yaml")
CANONICAL_CONTRACT = Path("contracts/api.yaml")


def test_canonical_contract_matches_feature_seed() -> None:
    feature = yaml.safe_load(FEATURE_SPEC.read_text(encoding="utf-8"))
    canonical = yaml.safe_load(CANONICAL_CONTRACT.read_text(encoding="utf-8"))

    assert feature["openapi"] == canonical["openapi"]
    assert feature["paths"].keys() <= canonical["paths"].keys()
