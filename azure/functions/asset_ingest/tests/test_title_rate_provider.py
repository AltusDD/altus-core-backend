import json
import os
import pathlib
import sys
import unittest
import types
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

try:
    import title_rate_handler
except ModuleNotFoundError as exc:
    if exc.name != "azure":
        raise

    azure_module = types.ModuleType("azure")
    functions_module = types.ModuleType("azure.functions")
    azure_module.functions = functions_module
    sys.modules["azure"] = azure_module
    sys.modules["azure.functions"] = functions_module
    import title_rate_handler

from title_rate_provider import (
    TitleRateProviderError,
    parse_title_rate_quote_request,
    quote_title_rate,
)


class TitleRateProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_provider = os.environ.get("PRICE_ENGINE_TITLE_RATE_PROVIDER")

    def tearDown(self) -> None:
        if self._original_provider is None:
            os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)
        else:
            os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = self._original_provider

    def test_parse_title_rate_quote_request_normalizes_defaults(self) -> None:
        request = parse_title_rate_quote_request(
            {
                "transactionType": "purchase",
                "propertyState": "mo",
                "county": "Jackson",
                "salesPrice": 425000,
                "loanAmount": 300000,
                "endorsements": ["T-19", " CPL "],
            }
        )

        self.assertEqual(request.transaction_type, "purchase")
        self.assertEqual(request.property_state, "MO")
        self.assertEqual(str(request.sales_price), "425000.0000")
        self.assertEqual(str(request.owner_policy_amount), "425000.0000")
        self.assertEqual(str(request.lender_policy_amount), "300000.0000")
        self.assertEqual(request.endorsements, ("T-19", "CPL"))
        self.assertEqual(request.county, "Jackson")
        self.assertEqual(request.city, None)

    def test_stub_provider_returns_normalized_quote(self) -> None:
        os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = "stub"

        response = quote_title_rate(
            {
                "transactionType": "purchase",
                "propertyState": "KS",
                "county": "Johnson",
                "city": "Overland Park",
                "postalCode": "66210",
                "salesPrice": 500000,
                "loanAmount": 400000,
                "endorsements": ["CPL"],
                "transactionDate": "2026-03-14",
                "providerContext": {"requestedProvider": "future-approved-provider"},
            }
        )

        self.assertEqual(response["providerKey"], "stub")
        self.assertEqual(response["status"], "stub")
        self.assertEqual(response["totals"]["total"], 0.0)
        self.assertEqual(response["lineItems"], [])
        self.assertEqual(
            response["providerContext"],
            {"mode": "stub", "requestedProvider": "future-approved-provider"},
        )
        self.assertTrue(response["warnings"])

    def test_no_provider_configured_behavior_is_explicit(self) -> None:
        os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)

        with self.assertRaises(TitleRateProviderError) as ctx:
            quote_title_rate(
                {
                    "transactionType": "purchase",
                    "propertyState": "MO",
                    "salesPrice": 425000,
                    "loanAmount": 300000,
                }
            )

        self.assertEqual(ctx.exception.code, "TITLE_RATE_PROVIDER_NOT_CONFIGURED")

    def test_handler_returns_501_when_no_provider_is_configured(self) -> None:
        os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)
        fake_request = _FakeHttpRequest(
            {
                "transactionType": "purchase",
                "propertyState": "MO",
                "salesPrice": 425000,
                "loanAmount": 300000,
            }
        )

        original_func = title_rate_handler.func
        title_rate_handler.func = SimpleNamespace(HttpResponse=_FakeHttpResponse)
        try:
            response = title_rate_handler.handle_title_rate_quote(
                fake_request,
                lambda: {"x-altus-build-sha": "test"},
            )
        finally:
            title_rate_handler.func = original_func

        self.assertEqual(response.status_code, 501)
        payload = json.loads(response.get_body().decode("utf-8"))
        self.assertEqual(payload["error"]["code"], "TITLE_RATE_PROVIDER_NOT_CONFIGURED")


class _FakeHttpRequest:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def get_json(self) -> dict:
        return self._payload


class _FakeHttpResponse:
    def __init__(self, body: str, status_code: int, headers: dict | None = None, mimetype: str | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.mimetype = mimetype
        self._body = body.encode("utf-8")

    def get_body(self) -> bytes:
        return self._body


if __name__ == "__main__":
    unittest.main()
