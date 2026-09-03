from pathlib import Path

import yaml

from app.main import app

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def test_documented_openapi_paths_match_fastapi_routes():
    documented_path = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.yaml"
    documented = yaml.safe_load(documented_path.read_text(encoding="utf-8"))["paths"]
    generated = {
        path.removeprefix("/api"): operations for path, operations in app.openapi()["paths"].items()
    }

    assert set(documented) == set(generated)
    for path, generated_operations in generated.items():
        generated_methods = HTTP_METHODS & set(generated_operations)
        documented_methods = HTTP_METHODS & set(documented[path])
        assert documented_methods == generated_methods
        for method in generated_methods:
            assert (
                documented[path][method]["operationId"]
                == generated_operations[method]["operationId"]
            )
