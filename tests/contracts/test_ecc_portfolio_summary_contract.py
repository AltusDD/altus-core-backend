from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / 'azure' / 'functions' / 'asset_ingest'
FIXTURE_ROOT = ROOT / 'docs' / 'contracts' / 'fixtures' / 'ecc_portfolio_summary'

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

import ecc_portfolio_summary_handler  # noqa: E402


class FakeRequest:
    def __init__(self, params: dict[str, str] | None = None):
        self.params = params or {}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class EccPortfolioSummaryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_portfolio_summary = ecc_portfolio_summary_handler.build_portfolio_summary

    def tearDown(self) -> None:
        ecc_portfolio_summary_handler.build_portfolio_summary = self.original_build_portfolio_summary

    def test_success_contract_matches_fixture(self) -> None:
        response = ecc_portfolio_summary_handler.handle_ecc_portfolio_summary(
            FakeRequest({'portfolioId': 'portfolio-001', 'asOfDate': '2026-03-13'}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-altus-build-sha'], 'test-sha')
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-summary')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.summary.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('success_response.json'),
        )

    def test_required_fields_and_deterministic_values(self) -> None:
        payload = json.loads(
            ecc_portfolio_summary_handler.handle_ecc_portfolio_summary(
                FakeRequest({'portfolioId': 'portfolio-001', 'asOfDate': '2026-03-13'}),
                lambda: {'x-altus-build-sha': 'test-sha'},
            ).get_body().decode('utf-8')
        )

        data = payload['data']
        self.assertEqual(data['portfolioId'], 'portfolio-001')
        self.assertEqual(data['asOfDate'], '2026-03-13')
        self.assertEqual(data['assetCount'], 13)
        self.assertEqual(data['occupiedUnits'], 48)
        self.assertEqual(data['totalUnits'], 52)
        self.assertEqual(data['occupancyRate'], 0.9230769230769231)
        self.assertEqual(data['estimatedValue'], 1625000.0)
        self.assertEqual(data['currency'], 'USD')
        self.assertEqual(data['activeAlerts'], 0)
        self.assertEqual(data['status'], 'stub_ready')

    def test_validation_failure_missing_portfolio_id_matches_fixture(self) -> None:
        response = ecc_portfolio_summary_handler.handle_ecc_portfolio_summary(
            FakeRequest({}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-summary')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.summary.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_missing_portfolio_id_response.json'),
        )

    def test_internal_error_contract_matches_fixture(self) -> None:
        def broken_build_portfolio_summary(portfolio_id: str, as_of: str | None) -> dict[str, object]:
            raise RuntimeError('boom')

        ecc_portfolio_summary_handler.build_portfolio_summary = broken_build_portfolio_summary

        response = ecc_portfolio_summary_handler.handle_ecc_portfolio_summary(
            FakeRequest({'portfolioId': 'portfolio-001'}),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-portfolio-summary')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.portfolio.summary.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_internal_response.json'),
        )


if __name__ == '__main__':
    unittest.main()
