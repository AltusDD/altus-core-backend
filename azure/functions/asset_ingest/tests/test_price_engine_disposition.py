import pathlib
import sys
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_disposition import build_disposition_metrics  # noqa: E402


class PriceEngineDispositionTests(unittest.TestCase):
    def test_disposition_stack_normalizes_percent_and_flat_costs(self) -> None:
        metrics = build_disposition_metrics(
            {
                "exitSalePrice": 225000,
                "saleCommissionRate": 0.06,
                "sellerClosingCostRate": 0.02,
                "dispositionFee": 1500,
                "sellerConcessions": 2500,
                "otherExitCosts": 1000,
            },
            default_sale_price=Decimal("220000"),
            exit_loan_payoff=Decimal("100895.0589175614"),
            legacy_selling_costs=Decimal("17600"),
        )

        self.assertEqual(metrics.gross_sale_proceeds, Decimal("225000"))
        self.assertEqual(metrics.sale_commission_cost.quantize(Decimal("0.01")), Decimal("13500.00"))
        self.assertEqual(metrics.seller_closing_cost.quantize(Decimal("0.01")), Decimal("4500.00"))
        self.assertEqual(metrics.total_exit_costs.quantize(Decimal("0.01")), Decimal("23000.00"))
        self.assertEqual(metrics.net_disposition_proceeds.quantize(Decimal("0.01")), Decimal("101104.94"))


if __name__ == "__main__":
    unittest.main()
