from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_ROOT = ROOT / 'azure' / 'functions' / 'asset_ingest'
FIXTURE_ROOT = ROOT / 'docs' / 'contracts' / 'fixtures' / 'price_engine_calculate'

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

from price_engine_handler import handle_price_engine_calculate  # noqa: E402


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding='utf-8'))


class FakeRequest:
    def __init__(self, payload=None, *, raises=False):
        self._payload = payload
        self._raises = raises

    def get_json(self):
        if self._raises:
            raise ValueError('invalid json')
        return self._payload


class PriceEngineCalculateContractTests(unittest.TestCase):
    def test_success_contract_matches_fixture(self) -> None:
        response = handle_price_engine_calculate(
            FakeRequest(load_fixture('success_request.json')),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-altus-build-sha'], 'test-sha')
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('success_response.json'),
        )

    def test_validation_failure_contract_matches_fixture(self) -> None:
        response = handle_price_engine_calculate(
            FakeRequest(load_fixture('error_missing_purchase_price_request.json')),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_missing_purchase_price_response.json'),
        )

    def test_named_error_behavior_matches_fixture(self) -> None:
        response = handle_price_engine_calculate(
            FakeRequest(load_fixture('error_unsupported_strategy_request.json')),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            load_fixture('error_unsupported_strategy_response.json'),
        )

    def test_invalid_json_is_wrapped_in_validation_error_envelope(self) -> None:
        response = handle_price_engine_calculate(
            FakeRequest(raises=True),
            lambda: {'x-altus-build-sha': 'test-sha'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_body().decode('utf-8')),
            {
                'error': {
                    'code': 'VALIDATION_FAILED',
                    'message': 'Request body must be valid JSON',
                    'details': None,
                }
            },
        )


if __name__ == '__main__':
    unittest.main()
