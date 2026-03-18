from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
FIXTURE_ROOT = ROOT / "docs" / "contracts" / "fixtures" / "price_engine_calculations_preview"

if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))


class FakeHttpResponse:
    def __init__(self, body, status_code=200, headers=None, mimetype=None):
        self._body = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.status_code = status_code
        self.headers = headers or {}
        self.mimetype = mimetype

    def get_body(self) -> bytes:
        return self._body


fake_func_module = types.SimpleNamespace(
    HttpResponse=FakeHttpResponse,
    HttpRequest=object,
)
fake_azure_module = types.SimpleNamespace(functions=fake_func_module)
sys.modules.setdefault("azure", fake_azure_module)
sys.modules.setdefault("azure.functions", fake_func_module)

from price_engine_calculations_preview_handler import handle_price_engine_calculations_preview  # noqa: E402


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class FakeRequest:
    def __init__(self, params=None):
        self.params = params or {}


class PriceEngineCalculationsPreviewContractTests(unittest.TestCase):
    def test_success_contract_matches_fixture(self) -> None:
        response = handle_price_engine_calculations_preview(
            FakeRequest(load_fixture("success_request.json")),
            lambda: {"x-altus-build-sha": "test-sha"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-altus-build-sha"], "test-sha")
        self.assertEqual(
            json.loads(response.get_body().decode("utf-8")),
            load_fixture("success_response.json"),
        )

    def test_validation_failure_contract_matches_fixture(self) -> None:
        response = handle_price_engine_calculations_preview(
            FakeRequest(load_fixture("error_missing_purchase_price_request.json")),
            lambda: {"x-altus-build-sha": "test-sha"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode("utf-8")),
            load_fixture("error_missing_purchase_price_response.json"),
        )


if __name__ == "__main__":
    unittest.main()
