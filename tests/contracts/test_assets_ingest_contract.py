from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / 'azure' / 'functions' / 'asset_ingest'
FIXTURE_ROOT = ROOT / 'docs' / 'contracts' / 'fixtures' / 'assets_ingest'

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


class FakeFunctionApp:
    def __init__(self, http_auth_level=None):
        self.http_auth_level = http_auth_level

    def route(self, **_kwargs):
        def decorator(func):
            return func

        return decorator


fake_functions_module = types.ModuleType('azure.functions')
fake_functions_module.FunctionApp = FakeFunctionApp
fake_functions_module.AuthLevel = types.SimpleNamespace(ANONYMOUS='ANONYMOUS')
fake_functions_module.HttpResponse = FakeHttpResponse
fake_functions_module.HttpRequest = object

fake_identity_module = types.ModuleType('azure.identity')
fake_identity_module.ManagedIdentityCredential = object

fake_secrets_module = types.ModuleType('azure.keyvault.secrets')
fake_secrets_module.SecretClient = object

fake_keyvault_module = types.ModuleType('azure.keyvault')
fake_keyvault_module.secrets = fake_secrets_module

fake_azure_module = types.ModuleType('azure')
fake_azure_module.functions = fake_functions_module
fake_azure_module.identity = fake_identity_module
fake_azure_module.keyvault = fake_keyvault_module

sys.modules['azure'] = fake_azure_module
sys.modules['azure.functions'] = fake_functions_module
sys.modules['azure.identity'] = fake_identity_module
sys.modules['azure.keyvault'] = fake_keyvault_module
sys.modules['azure.keyvault.secrets'] = fake_secrets_module

fake_requests_module = types.ModuleType('requests')
fake_requests_module.post = None
sys.modules['requests'] = fake_requests_module

for module_name, function_name in {
    'ecc_portfolio_summary_handler': 'handle_ecc_portfolio_summary',
    'ecc_portfolio_assets_handler': 'handle_ecc_portfolio_assets',
    'ecc_asset_search_handler': 'handle_ecc_asset_search',
    'ecc_asset_metrics_handler': 'handle_ecc_asset_metrics',
    'ecc_system_health_handler': 'handle_ecc_system_health',
    'price_engine_handler': 'handle_price_engine_calculate',
}.items():
    module = types.ModuleType(module_name)

    def _stub(req, build_headers):
        return None

    setattr(module, function_name, _stub)
    sys.modules[module_name] = module

import function_app  # noqa: E402


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class FakeRequest:
    def __init__(self, headers: dict[str, str] | None = None, payload=None):
        self.headers = headers or {}
        self._payload = payload

    def get_json(self):
        return self._payload


class AssetsIngestContractTests(unittest.TestCase):
    def setUp(self) -> None:
        function_app._config = None
        self.original_get_config = function_app._get_config
        self.original_insert = function_app._insert_supabase_row

    def tearDown(self) -> None:
        function_app._get_config = self.original_get_config
        function_app._insert_supabase_row = self.original_insert
        function_app._config = None

    def test_success_contract_matches_fixture(self) -> None:
        request_fixture = load_fixture('success_request.json')
        expected_response = load_fixture('success_response.json')
        insert_calls: list[tuple[str, dict[str, object]]] = []

        def fake_insert(table: str, payload: dict[str, object], config) -> dict[str, object]:
            insert_calls.append((table, payload))
            if table == 'assets':
                return {'id': expected_response['asset_id']}
            if table == 'asset_data_raw':
                return {'id': expected_response['raw_id']}
            raise AssertionError(f'unexpected table {table}')

        function_app._get_config = lambda: object()
        function_app._insert_supabase_row = fake_insert

        response = function_app.assets_ingest(
            FakeRequest(request_fixture['headers'], request_fixture['body'])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.get_body().decode('utf-8')), expected_response)
        self.assertEqual([call[0] for call in insert_calls], ['assets', 'asset_data_raw'])
        self.assertEqual(
            insert_calls[0][1]['organization_id'],
            request_fixture['headers']['x-altus-org-id'],
        )
        self.assertEqual(
            insert_calls[1][1]['payload_sha256'],
            expected_response['payload_hash'],
        )

    def test_validation_failure_missing_header_matches_fixture(self) -> None:
        request_fixture = load_fixture('error_missing_header_request.json')

        response = function_app.assets_ingest(
            FakeRequest(request_fixture['headers'], request_fixture['body'])
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_missing_header_response.json'),
        )

    def test_validation_failure_invalid_source_matches_fixture(self) -> None:
        request_fixture = load_fixture('error_invalid_source_request.json')

        response = function_app.assets_ingest(
            FakeRequest(request_fixture['headers'], request_fixture['body'])
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_invalid_source_response.json'),
        )

    def test_internal_error_contract_matches_fixture(self) -> None:
        request_fixture = load_fixture('success_request.json')

        def broken_insert(table: str, payload: dict[str, object], config) -> dict[str, object]:
            raise RuntimeError('boom')

        function_app._get_config = lambda: object()
        function_app._insert_supabase_row = broken_insert

        response = function_app.assets_ingest(
            FakeRequest(request_fixture['headers'], request_fixture['body'])
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_internal_response.json'),
        )


if __name__ == '__main__':
    unittest.main()
