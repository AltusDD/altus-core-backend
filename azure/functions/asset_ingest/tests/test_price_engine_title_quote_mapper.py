import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_title_quote_mapper import map_title_quote_to_calculation_inputs  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
