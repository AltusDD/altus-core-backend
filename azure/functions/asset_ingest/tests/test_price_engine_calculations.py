import pathlib
import sys
import unittest
from decimal import Decimal
import os

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_calculations import (  # noqa: E402
    build_deal_inputs,
    calculate_cash_on_cash,
    calculate_irr,
    calculate_mao,
    calculate_total_lender_fees,
    calculate_total_title_fees,
    calculate_total_transaction_costs,
)
from price_engine_service import calculate_price_engine  # noqa: E402


class PriceEngineCalculationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_provider = os.environ.get("PRICE_ENGINE_TITLE_RATE_PROVIDER")

    def tearDown(self) -> None:
        if self._original_provider is None:
            os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)
        else:
            os.environ["PRICE_ENGINE_TITLE_RATE_PROVIDER"] = self._original_provider

    def test_core_formulas_produce_expected_outputs(self) -> None:
        inputs = build_deal_inputs(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "titlePremium": 1800,
                "settlementFee": 850,
                "recordingFee": 225,
                "ownerPolicy": 450,
                "lenderPolicy": 375,
            }
        )

        self.assertEqual(calculate_total_lender_fees(inputs).quantize(Decimal("0.01")), Decimal("3825.00"))
        self.assertEqual(calculate_total_title_fees(inputs).quantize(Decimal("0.01")), Decimal("3700.00"))
        self.assertEqual(calculate_total_transaction_costs(inputs).quantize(Decimal("0.01")), Decimal("14525.00"))
        self.assertEqual(calculate_mao(inputs).quantize(Decimal("0.01")), Decimal("123475.00"))
        self.assertEqual(calculate_cash_on_cash(inputs).quantize(Decimal("0.01")), Decimal("28.02"))
        self.assertEqual(calculate_irr(inputs).quantize(Decimal("0.01")), Decimal("93.92"))

    def test_service_uses_stub_title_quote_when_provider_is_unavailable(self) -> None:
        os.environ.pop("PRICE_ENGINE_TITLE_RATE_PROVIDER", None)

        metrics = calculate_price_engine(
            {
                "strategy": "flip",
                "purchasePrice": 120000,
                "afterRepairValue": 220000,
                "rehabCost": 30000,
                "holdingCosts": 8000,
                "closingCosts": 7000,
                "cashAvailable": 60000,
                "rentMonthly": 2500,
                "operatingExpenseMonthly": 900,
                "targetProfitMargin": 0.12,
                "loanOriginationFee": 1500,
                "underwritingFee": 995,
                "processingFee": 695,
                "appraisalFee": 550,
                "creditReportFee": 85,
                "propertyState": "MO",
                "county": "Jackson",
                "city": "Kansas City",
                "postalCode": "64108",
                "endorsements": ["CPL", "T-19"],
                "transactionDate": "2026-03-18",
                "titlePremium": 1800,
                "settlementFee": 850,
                "recordingFee": 225,
                "ownerPolicy": 450,
                "lenderPolicy": 375,
            }
        )

        self.assertEqual(metrics["TotalLenderFees"], 3825.0)
        self.assertEqual(metrics["TotalTitleFees"], 0.0)
        self.assertEqual(metrics["TotalTransactionCosts"], 10825.0)
        self.assertEqual(metrics["CashToClose"], 64825.0)


if __name__ == "__main__":
    unittest.main()
