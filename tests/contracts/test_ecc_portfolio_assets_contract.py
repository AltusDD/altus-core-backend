from __future__ import annotations

import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

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
import ecc_portfolio_assets_service  # noqa: E402


class FakeRequest:
    def __init__(self, params: dict[str, str] | None = None):
        self.params = params or {}


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class FakeBackingSource:
    def __init__(self, payload):
        self._payload = payload

    def read_rows(self, portfolio_id: str, limit: int, offset: int):
        return self._payload


class FakeUrlOpenResponse:
    def __init__(self, body, content_range: str = ''):
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
        self.headers = {'Content-Range': content_range} if content_range else {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class EccPortfolioAssetsContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_portfolio_assets = ecc_portfolio_assets_handler.build_portfolio_assets
        self.original_default_backing_source = ecc_portfolio_assets_service._build_default_backing_source

    def tearDown(self) -> None:
        ecc_portfolio_assets_handler.build_portfolio_assets = self.original_build_portfolio_assets
        ecc_portfolio_assets_service._build_default_backing_source = self.original_default_backing_source

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

    def test_fallback_remains_intact_when_backing_source_is_not_proven(self) -> None:
        ecc_portfolio_assets_service._build_default_backing_source = lambda: FakeBackingSource(None)

        payload = ecc_portfolio_assets_service.build_portfolio_assets('portfolio-001', 2, 1)

        self.assertEqual(payload, load_fixture('success_response.json'))

    def test_backed_fields_can_override_stub_subset_without_contract_shape_drift(self) -> None:
        ecc_portfolio_assets_service._build_default_backing_source = lambda: FakeBackingSource(
            ecc_portfolio_assets_service.PortfolioAssetsBackingPayload(
                rows=[
                    ecc_portfolio_assets_service.PortfolioAssetsBackingRow(
                        asset_id='asset-db-001',
                        display_name='Live Asset One',
                        asset_type='industrial',
                        status='active',
                        total_units=23,
                    ),
                    ecc_portfolio_assets_service.PortfolioAssetsBackingRow(
                        asset_id='asset-db-002',
                        display_name='Live Asset Two',
                        asset_type=None,
                        status='inactive',
                        total_units=None,
                    ),
                ],
                total=2,
            )
        )

        payload = ecc_portfolio_assets_service.build_portfolio_assets('portfolio-001', 2, 1)
        fixture = load_fixture('success_response.json')

        self.assertEqual(set(payload.keys()), set(fixture.keys()))
        self.assertEqual(payload['meta']['portfolioId'], 'portfolio-001')
        self.assertEqual(payload['meta']['limit'], 2)
        self.assertEqual(payload['meta']['offset'], 1)
        self.assertEqual(payload['meta']['total'], 2)
        self.assertEqual(len(payload['data']), 2)
        self.assertEqual(set(payload['data'][0].keys()), set(fixture['data'][0].keys()))
        self.assertEqual(payload['data'][0]['assetId'], 'asset-db-001')
        self.assertEqual(payload['data'][0]['displayName'], 'Live Asset One')
        self.assertEqual(payload['data'][0]['assetType'], 'industrial')
        self.assertEqual(payload['data'][0]['status'], 'active')
        self.assertEqual(payload['data'][0]['totalUnits'], 23)
        self.assertEqual(payload['data'][0]['occupiedUnits'], 7)
        self.assertEqual(payload['data'][1]['assetId'], 'asset-db-002')
        self.assertEqual(payload['data'][1]['displayName'], 'Live Asset Two')
        self.assertEqual(payload['data'][1]['assetType'], 'multifamily')
        self.assertEqual(payload['data'][1]['status'], 'inactive')
        self.assertEqual(payload['data'][1]['totalUnits'], 10)
        self.assertEqual(payload['data'][1]['occupiedUnits'], 10)

    def test_default_backing_source_uses_shared_supabase_config_when_mapping_key_is_present(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                'SUPABASE_URL': 'https://example.supabase.co',
                'SUPABASE_SERVICE_ROLE_KEY': 'service-role-key',
                'ALTUS_ECC_PORTFOLIO_ASSETS_PORTFOLIO_ID_EXTERNAL_IDS_KEY': 'portfolio_id',
            },
            clear=True,
        ):
            source = ecc_portfolio_assets_service._build_default_backing_source()

        self.assertIsInstance(source, ecc_portfolio_assets_service._AssetsExternalIdsPortfolioAssetsSource)
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
            source = ecc_portfolio_assets_service._build_default_backing_source()

        self.assertIsInstance(source, ecc_portfolio_assets_service._NoopPortfolioAssetsBackingSource)

    def test_external_ids_resolver_reads_live_row_subset_from_resolved_cohort(self) -> None:
        captured = []
        resolver = ecc_portfolio_assets_service._AssetsExternalIdsPortfolioAssetsSource(
            'https://example.supabase.co',
            'service-role-key',
            'portfolio_id',
        )

        def fake_urlopen(request, timeout):
            captured.append((request.full_url, timeout))
            if '/rest/v1/assets?' in request.full_url:
                return FakeUrlOpenResponse(
                    [
                        {'id': 'asset-1', 'display_name': 'Asset One', 'status': 'active'},
                        {'id': 'asset-2', 'display_name': 'Asset Two', 'asset_type': 'storage', 'status': 'inactive'},
                    ],
                    '1-2/7',
                )
            return FakeUrlOpenResponse(
                [
                    {'asset_id': 'asset-1', 'units_count': 12},
                    {'asset_id': 'asset-2', 'units_count': 30},
                ]
            )

        with mock.patch.object(ecc_portfolio_assets_service, 'urlopen', side_effect=fake_urlopen):
            payload = resolver.read_rows('portfolio-001', 2, 1)

        self.assertEqual(payload.total, 7)
        self.assertEqual(len(payload.rows), 2)
        self.assertEqual(payload.rows[0].asset_id, 'asset-1')
        self.assertEqual(payload.rows[0].display_name, 'Asset One')
        self.assertIsNone(payload.rows[0].asset_type)
        self.assertEqual(payload.rows[0].status, 'active')
        self.assertEqual(payload.rows[0].total_units, 12)
        self.assertEqual(payload.rows[1].asset_id, 'asset-2')
        self.assertEqual(payload.rows[1].asset_type, 'storage')
        self.assertEqual(payload.rows[1].total_units, 30)
        self.assertEqual(captured[0][1], 10)
        self.assertIn('external_ids-%3E%3Eportfolio_id=eq.portfolio-001', captured[0][0])
        self.assertIn('limit=2', captured[0][0])
        self.assertIn('offset=1', captured[0][0])
        self.assertIn('/rest/v1/asset_specs_reconciled?', captured[1][0])

    def test_external_ids_resolver_preserves_row_level_fallback_when_units_are_missing(self) -> None:
        resolver = ecc_portfolio_assets_service._AssetsExternalIdsPortfolioAssetsSource(
            'https://example.supabase.co',
            'service-role-key',
            'portfolio_id',
        )

        def fake_urlopen(request, timeout):
            if '/rest/v1/assets?' in request.full_url:
                return FakeUrlOpenResponse(
                    [{'id': 'asset-1', 'display_name': 'Asset One', 'status': 'active'}],
                    '0-0/1',
                )
            return FakeUrlOpenResponse([{'asset_id': 'asset-1', 'units_count': None}])

        with mock.patch.object(ecc_portfolio_assets_service, 'urlopen', side_effect=fake_urlopen):
            payload = resolver.read_rows('portfolio-001', 1, 0)

        self.assertEqual(payload.total, 1)
        self.assertIsNone(payload.rows[0].total_units)

    def test_external_ids_resolver_returns_none_for_invalid_content_range(self) -> None:
        resolver = ecc_portfolio_assets_service._AssetsExternalIdsPortfolioAssetsSource(
            'https://example.supabase.co',
            'service-role-key',
            'portfolio_id',
        )

        with mock.patch.object(
            ecc_portfolio_assets_service,
            'urlopen',
            return_value=FakeUrlOpenResponse([], 'invalid'),
        ):
            payload = resolver.read_rows('portfolio-001', 2, 1)

        self.assertIsNone(payload)


if __name__ == '__main__':
    unittest.main()
