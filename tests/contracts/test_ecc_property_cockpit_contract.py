from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
FIXTURE_ROOT = ROOT / "docs" / "contracts" / "fixtures" / "ecc_property_cockpit"

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

import ecc_property_cockpit_handler  # noqa: E402


class FakeRequest:
    def __init__(self, params: dict[str, str] | None = None):
        self.params = params or {}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


class EccPropertyCockpitContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_property_cockpit = ecc_property_cockpit_handler.build_property_cockpit

    def tearDown(self) -> None:
        ecc_property_cockpit_handler.build_property_cockpit = self.original_build_property_cockpit

    def test_success_contract_matches_fixture(self) -> None:
        ecc_property_cockpit_handler.build_property_cockpit = lambda asset_id, deal_id, transaction_id: load_fixture(
            "success_response.json"
        )

        response = ecc_property_cockpit_handler.handle_ecc_property_cockpit(
            FakeRequest({"assetId": "asset-001", "dealId": "deal-001", "transactionId": "txn-001"}),
            lambda: {"x-altus-build-sha": "test-sha"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-altus-build-sha"], "test-sha")
        self.assertEqual(response.headers["x-ecc-handler"], "ecc-property-cockpit")
        self.assertEqual(response.headers["x-ecc-domain-signature"], "ecc.property.cockpit.v1")
        self.assertEqual(
            json.loads(response.get_body().decode("utf-8")),
            load_fixture("success_response.json"),
        )

    def test_validation_failure_missing_asset_id_matches_fixture(self) -> None:
        response = ecc_property_cockpit_handler.handle_ecc_property_cockpit(
            FakeRequest({}),
            lambda: {"x-altus-build-sha": "test-sha"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["x-ecc-handler"], "ecc-property-cockpit")
        self.assertEqual(response.headers["x-ecc-domain-signature"], "ecc.property.cockpit.v1")
        self.assertEqual(
            json.loads(response.get_body().decode("utf-8")),
            load_fixture("error_missing_asset_id_response.json"),
        )

    def test_internal_error_contract_matches_fixture(self) -> None:
        def broken_build_property_cockpit(asset_id: str, deal_id: str | None, transaction_id: str | None):
            raise RuntimeError("boom")

        ecc_property_cockpit_handler.build_property_cockpit = broken_build_property_cockpit

        response = ecc_property_cockpit_handler.handle_ecc_property_cockpit(
            FakeRequest({"assetId": "asset-001"}),
            lambda: {"x-altus-build-sha": "test-sha"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["x-ecc-handler"], "ecc-property-cockpit")
        self.assertEqual(response.headers["x-ecc-domain-signature"], "ecc.property.cockpit.v1")
        self.assertEqual(
            json.loads(response.get_body().decode("utf-8")),
            load_fixture("error_internal_response.json"),
        )


if __name__ == "__main__":
    unittest.main()
