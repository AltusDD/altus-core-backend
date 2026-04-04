import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_errors import PriceEngineError  # noqa: E402
from price_engine_input_normalization import normalize_price_engine_payload  # noqa: E402


class PriceEngineInputNormalizationTests(unittest.TestCase):
    def test_flip_preset_populates_missing_fields_without_overriding_explicit_values(self) -> None:
        normalized = normalize_price_engine_payload(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "holdingMonths": 12,
            }
        )

        self.assertEqual(normalized.scenario_profile, "flip")
        self.assertEqual(normalized.payload["holdingMonths"], 12)
        self.assertIn("annualInterestRate", normalized.applied_preset_fields)
        self.assertIn("interestOnly", normalized.applied_preset_fields)
        self.assertIn("saleCommissionRate", normalized.applied_preset_fields)
        self.assertTrue(normalized.validation_warnings)
        self.assertIn("Scenario preset defaults were applied", normalized.validation_warnings[0])

    def test_rental_hold_preset_populates_expected_defaults(self) -> None:
        normalized = normalize_price_engine_payload(
            {
                "strategy": "rental_hold",
                "purchasePrice": 185000,
                "afterRepairValue": 235000,
                "rehabCost": 15000,
                "holdingCosts": 6000,
                "closingCosts": 5000,
                "cashAvailable": 70000,
            }
        )

        self.assertEqual(normalized.scenario_profile, "rental_hold")
        self.assertEqual(normalized.payload["holdingMonths"], 12)
        self.assertEqual(normalized.payload["annualInterestRate"], 0.075)
        self.assertEqual(normalized.payload["interestOnly"], False)
        self.assertEqual(normalized.payload["amortizationMonths"], 360)
        self.assertIn("targetProfitMargin", normalized.applied_preset_fields)

    def test_brrrr_preset_populates_expected_defaults(self) -> None:
        normalized = normalize_price_engine_payload(
            {
                "strategy": "brrrr",
                "purchasePrice": 140000,
                "afterRepairValue": 210000,
                "rehabCost": 25000,
                "holdingCosts": 7000,
                "closingCosts": 6500,
                "cashAvailable": 55000,
            }
        )

        self.assertEqual(normalized.scenario_profile, "brrrr")
        self.assertEqual(normalized.payload["holdingMonths"], 9)
        self.assertEqual(normalized.payload["annualInterestRate"], 0.085)
        self.assertEqual(normalized.payload["interestOnly"], True)
        self.assertIn("sellerClosingCostRate", normalized.applied_preset_fields)

    def test_invalid_points_rate_is_rejected(self) -> None:
        with self.assertRaises(PriceEngineError) as ctx:
            normalize_price_engine_payload(
                {
                    "strategy": "flip",
                    "purchasePrice": 120000,
                    "afterRepairValue": 220000,
                    "rehabCost": 30000,
                    "holdingCosts": 8000,
                    "closingCosts": 7000,
                    "cashAvailable": 60000,
                    "pointsRate": 0.50,
                }
            )

        self.assertEqual(ctx.exception.code, "VALIDATION_FAILED")
        self.assertIn("pointsRate", ctx.exception.message)

    def test_invalid_annual_interest_rate_is_rejected(self) -> None:
        with self.assertRaises(PriceEngineError) as ctx:
            normalize_price_engine_payload(
                {
                    "strategy": "flip",
                    "purchasePrice": 120000,
                    "afterRepairValue": 220000,
                    "rehabCost": 30000,
                    "holdingCosts": 8000,
                    "closingCosts": 7000,
                    "cashAvailable": 60000,
                    "annualInterestRate": 1.25,
                }
            )

        self.assertEqual(ctx.exception.code, "VALIDATION_FAILED")
        self.assertIn("annualInterestRate", ctx.exception.message)

    def test_non_positive_holding_months_is_rejected(self) -> None:
        with self.assertRaises(PriceEngineError) as ctx:
            normalize_price_engine_payload(
                {
                    "strategy": "flip",
                    "purchasePrice": 120000,
                    "afterRepairValue": 220000,
                    "rehabCost": 30000,
                    "holdingCosts": 8000,
                    "closingCosts": 7000,
                    "cashAvailable": 60000,
                    "holdingMonths": 0,
                }
            )

        self.assertEqual(ctx.exception.code, "VALIDATION_FAILED")
        self.assertIn("holdingMonths", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
