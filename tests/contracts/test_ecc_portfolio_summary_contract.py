from __future__ import annotations

import json
import os
import sys
import types
import unittest
from unittest import mock
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
import ecc_portfolio_summary_service  # noqa: E402


class FakeRequest:
    def __init__(self, params: dict[str, str] | None = None):
        self.params = params or {}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class FakeBackingSource:
    def __init__(self, fields):
        self._fields = fields

    def read_fields(self, portfolio_id: str, as_of: str | None):
        return self._fields


class FakeUrlOpenResponse:
    def __init__(self, content_range: str):
        self.headers = {'Content-Range': content_range}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

class EccPortfolioSummaryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_portfolio_summary = ecc_portfolio_summary_handler.build_portfolio_summary
        self.original_default_backing_source = ecc_portfolio_summary_service._build_default_backing_source

    def tearDown(self) -> None:
        ecc_portfolio_summary_handler.build_portfolio_summary = self.original_build_portfolio_summary
        ecc_portfolio_summary_service._build_default_backing_source = self.original_default_backing_source

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

    def test_fallback_remains_intact_when_backing_source_is_not_proven(self) -> None:
        ecc_portfolio_summary_service._build_default_backing_source = lambda: FakeBackingSource(None)

        payload = ecc_portfolio_summary_service.build_portfolio_summary('portfolio-001', '2026-03-13')

        self.assertEqual(payload, load_fixture('success_response.json')['data'])

    def test_asset_count_can_be_backed_without_contract_shape_drift(self) -> None:
        ecc_portfolio_summary_service._build_default_backing_source = lambda: FakeBackingSource(
            ecc_portfolio_summary_service.PortfolioSummaryBackingFields(asset_count=27)
        )

        payload = ecc_portfolio_summary_service.build_portfolio_summary('portfolio-001', '2026-03-13')

        self.assertEqual(set(payload.keys()), set(load_fixture('success_response.json')['data'].keys()))
        self.assertEqual(payload['assetCount'], 27)
        self.assertEqual(payload['portfolioId'], 'portfolio-001')
        self.assertEqual(payload['asOfDate'], '2026-03-13')
        self.assertEqual(payload['status'], 'stub_ready')
        self.assertEqual(payload['currency'], 'USD')

    def test_default_backing_source_uses_shared_supabase_config_when_mapping_key_is_present(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                'SUPABASE_URL': 'https://example.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'service-role-key',
                'ALTUS_ECC_PORTFOLIO_SUMMARY_PORTFOLIO_ID_EXTERNAL_IDS_KEY': 'portfolio_id',
            },
            clear=True,
        ):
            source = ecc_portfolio_summary_service._build_default_backing_source()

        self.assertIsInstance(source, ecc_portfolio_summary_service._AssetsExternalIdsPortfolioCohortResolver)
        self.assertEqual(source._supabase_url, 'https://example.supabase.co')
        self.assertEqual(source._service_role_key, 'service-role-key')
        self.assertEqual(source._external_ids_key, 'portfolio_id')

    def test_default_backing_source_remains_noop_when_mapping_key_is_missing(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                'SUPABASE_URL': 'https://example.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'service-role-key',
            },
            clear=True,
        ):
            source = ecc_portfolio_summary_service._build_default_backing_source()

        self.assertIsInstance(source, ecc_portfolio_summary_service._NoopPortfolioSummaryBackingSource)

    def test_external_ids_resolver_reads_asset_count_from_content_range(self) -> None:
        captured = {}
        resolver = ecc_portfolio_summary_service._AssetsExternalIdsPortfolioCohortResolver(
            'https://example.supabase.co',
            'service-role-key',
            'portfolio_id',
        )

        def fake_urlopen(request, timeout):
            captured['url'] = request.full_url
            captured['timeout'] = timeout
            return FakeUrlOpenResponse('0-0/27')

        with mock.patch.object(ecc_portfolio_summary_service, 'urlopen', side_effect=fake_urlopen):
            fields = resolver.read_fields('portfolio-001', None)

        self.assertEqual(fields.asset_count, 27)
        self.assertEqual(captured['timeout'], 10)
        self.assertIn('external_ids-%3E%3Eportfolio_id=eq.portfolio-001', captured['url'])

    def test_external_ids_resolver_returns_none_for_invalid_content_range(self) -> None:
        resolver = ecc_portfolio_summary_service._AssetsExternalIdsPortfolioCohortResolver(
            'https://example.supabase.co',
            'service-role-key',
            'portfolio_id',
        )

        with mock.patch.object(
            ecc_portfolio_summary_service,
            'urlopen',
            return_value=FakeUrlOpenResponse('invalid'),
        ):
            fields = resolver.read_fields('portfolio-001', None)

        self.assertIsNone(fields)

if __name__ == '__main__':
    unittest.main()

