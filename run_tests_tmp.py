import pytest, sys

if __name__ == "__main__":
    sys.exit(
        pytest.main([
            "backend/tests/unit/test_core_tenant_model.py",
            "backend/tests/unit/test_core_tenant_middleware.py",
            "--maxfail=1",
            "-q",
        ])
    )
