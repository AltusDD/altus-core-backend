from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / 'azure' / 'functions' / 'asset_ingest'
FIXTURE_ROOT = ROOT / 'docs' / 'contracts' / 'fixtures' / 'ecc_system_health'

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

import ecc_system_health_handler  # noqa: E402


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class EccSystemHealthContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_build_system_health = ecc_system_health_handler.build_system_health

    def tearDown(self) -> None:
        ecc_system_health_handler.build_system_health = self.original_build_system_health

    def test_success_contract_matches_fixture(self) -> None:
        response = ecc_system_health_handler.handle_ecc_system_health(
            object(),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-altus-build-sha'], 'test-sha')
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-system-health')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.system.health.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('success_response.json'),
        )

    def test_required_fields_and_deterministic_component_order(self) -> None:
        payload = json.loads(
            ecc_system_health_handler.handle_ecc_system_health(
                object(),
                lambda: {'x-altus-build-sha': 'test-sha'},
            ).get_body().decode('utf-8')
        )

        data = payload['data']
        self.assertEqual(data['status'], 'operational')
        self.assertIsNone(data['generatedAt'])
        self.assertEqual(data['activeIncidents'], 1)
        self.assertEqual(
            [component['name'] for component in data['components']],
            ['assetIndex', 'portfolioCache', 'priceEngine'],
        )
        self.assertEqual(
            [component['status'] for component in data['components']],
            ['operational', 'operational', 'degraded'],
        )

    def test_internal_error_contract_matches_fixture(self) -> None:
        def broken_system_health() -> dict[str, object]:
            raise RuntimeError('boom')

        ecc_system_health_handler.build_system_health = broken_system_health

        response = ecc_system_health_handler.handle_ecc_system_health(
            object(),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers['x-ecc-handler'], 'ecc-system-health')
        self.assertEqual(response.headers['x-ecc-domain-signature'], 'ecc.system.health.v1')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_internal_response.json'),
        )


if __name__ == '__main__':
    unittest.main()
