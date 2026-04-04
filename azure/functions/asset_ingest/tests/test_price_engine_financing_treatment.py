import pathlib
import sys
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_financing_treatment import build_financing_treatment  # noqa: E402


class PriceEngineFinancingTreatmentTests(unittest.TestCase):
    def test_points_rate_and_financing_flags_are_normalized(self) -> None:
        treatment = build_financing_treatment(
            {
                "pointsRate": 0.02,
                "financeLenderFees": True,
                "financeTitleFees": False,
                "financePoints": True,
            },
            loan_amount=Decimal("96000"),
            total_lender_fees=Decimal("3825"),
            total_title_fees=Decimal("1200"),
            explicit_points=Decimal("0"),
        )

        self.assertEqual(treatment.total_points, Decimal("1920.00"))
        self.assertEqual(treatment.cash_paid_lender_fees, Decimal("0"))
        self.assertEqual(treatment.financed_lender_fees, Decimal("3825"))
        self.assertEqual(treatment.cash_paid_title_fees, Decimal("1200"))
        self.assertEqual(treatment.financed_title_fees, Decimal("0"))
        self.assertEqual(treatment.cash_paid_points, Decimal("0.00"))
        self.assertEqual(treatment.financed_points, Decimal("1920.00"))
        self.assertEqual(treatment.cash_paid_transaction_costs, Decimal("1200.00"))
        self.assertEqual(treatment.financed_transaction_costs, Decimal("5745.00"))
        self.assertEqual(treatment.effective_loan_payoff, Decimal("101745.00"))


if __name__ == "__main__":
    unittest.main()
