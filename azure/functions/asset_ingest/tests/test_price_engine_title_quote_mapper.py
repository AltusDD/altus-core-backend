import pathlib
import sys
import unittest
import json

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_title_quote_mapper import build_title_quote_request_payload, map_title_quote_to_calculation_inputs  # noqa: E402
from price_engine_calculations import build_deal_inputs  # noqa: E402


class PriceEngineTitleQuoteMapperTests(unittest.TestCase):
    def test_mapper_derives_title_premium_from_remaining_quote_total(self) -> None:
        mapped = map_title_quote_to_calculation_inputs(
            {
                "totals": {
                    "ownerPolicy": 450.0,
                    "lenderPolicy": 375.0,
                    "settlementServices": 850.0,
                    "recordingFees": 225.0,
                    "endorsements": 300.0,
                    "transferTaxes": 125.0,
                    "otherFees": 50.0,
                    "total": 2375.0,
                }
            }
        )

        self.assertEqual(
            mapped,
            {
                "titlePremium": 475.0,
                "settlementFee": 850.0,
                "recordingFee": 225.0,
                "ownerPolicy": 450.0,
                "lenderPolicy": 375.0,
            },
        )

    def test_request_payload_parses_provider_context_json_for_preview_safe_usage(self) -> None:
        inputs = build_deal_inputs(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
            }
        )

        payload = build_title_quote_request_payload(
            {
                "propertyState": "MO",
                "providerContext": json.dumps(
                    {
                        "requestedProvider": "liberty",
                        "libertySnapshot": {
                            "quoteReference": "LIA-QUOTE-001",
                            "snapshotVersion": "v1",
                            "fees": {
                                "titlePremium": 1800,
                                "settlementFee": 850,
                                "recordingFee": 225,
                                "ownerPolicy": 450,
                                "lenderPolicy": 375,
                            },
                        },
                    }
                ),
            },
            inputs,
        )

        self.assertEqual(payload["providerContext"]["requestedProvider"], "liberty")
        self.assertEqual(payload["providerContext"]["libertySnapshot"]["fees"]["titlePremium"], 1800)


if __name__ == "__main__":
    unittest.main()
