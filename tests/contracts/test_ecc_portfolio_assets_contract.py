from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / 'azure' / 'functions' / 'asset_ingest'
FIXTURE_ROOT = ROOT / 'docs' / 'contracts' / 'fixtures' / 'ecc_portfolio_assets'

if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))


class FakeHttpResponse:
    def __init__(self, body, status_code=200, headers=None, mimetype=None):
        self._body = body if isinstance(body, bytes) else str(body).encode('utf-8')
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
sys.modules.setdefault('azure', fake_azure_module)
sys.modules.setdefault('azure.functions', fake_func_module)

import ecc_portfolio_assets_handler  # noqa: E402


class FakeRequest:
    def __init__(self, params: dict[str, str] | None = None):
        self.params = params or {}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class EccPortfolioAssetsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_portfolio_assets = ecc_portfolio_assets_handler.build_portfolio_assets

    def tearDown(self) -> None:
        ecc_portfolio_assets_handler.build_portfolio_assets = self.original_build_portfolio_assets

    def test_success_contract_matches_fixture(self) -> None:
        response = ecc_portfolio_assets_handler.handle_ecc_portfolio_assets(
            FakeRequest({'portfolioId': 'portfolio-001', 'limit': '2', 'offset': '1'}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-altus-build-sha'], 'test-sha')
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-assets')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.assets.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('success_response.json'),
        )

    def test_required_fields_and_deterministic_values(self) -> None:
        payload = json.loads(
            ecc_portfolio_assets_handler.handle_ecc_portfolio_assets(
                FakeRequest({'portfolioId': 'portfolio-001', 'limit': '2', 'offset': '1'}),
                lambda: {'x-altus-build-sha': 'test-sha'},
            ).get_body().decode('utf-8')
        )

        self.assertEqual(payload['meta']['portfolioId'], 'portfolio-001')
        self.assertEqual(payload['meta']['limit'], 2)
        self.assertEqual(payload['meta']['offset'], 1)
        self.assertEqual(payload['meta']['total'], 13)
        self.assertEqual(len(payload['data']), 2)
        self.assertEqual(payload['data'][0]['assetId'], 'portfolio-001-asset-002')
        self.assertEqual(payload['data'][0]['occupiedUnits'], 7)
        self.assertEqual(payload['data'][0]['totalUnits'], 9)
        self.assertEqual(payload['data'][1]['assetId'], 'portfolio-001-asset-003')
        self.assertEqual(payload['data'][1]['occupiedUnits'], 10)
        self.assertEqual(payload['data'][1]['totalUnits'], 10)

    def test_validation_failure_missing_portfolio_id_matches_fixture(self) -> None:
        response = ecc_portfolio_assets_handler.handle_ecc_portfolio_assets(
            FakeRequest({}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-assets')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.assets.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_missing_portfolio_id_response.json'),
        )

    def test_validation_failure_invalid_pagination_matches_fixture(self) -> None:
        response = ecc_portfolio_assets_handler.handle_ecc_portfolio_assets(
            FakeRequest({'portfolioId': 'portfolio-001', 'limit': '101', 'offset': '-1'}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_invalid_pagination_response.json'),
        )

    def test_internal_error_contract_matches_fixture(self) -> None:
        def broken_build_portfolio_assets(portfolio_id: str, limit: int, offset: int) -> dict[str, object]:
            raise RuntimeError('boom')

        ecc_portfolio_assets_handler.build_portfolio_assets = broken_build_portfolio_assets

        response = ecc_portfolio_assets_handler.handle_ecc_portfolio_assets(
            FakeRequest({'portfolioId': 'portfolio-001'}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-assets')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.assets.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_internal_response.json'),
        )


if __name__ == '__main__':
    unittest.main()
