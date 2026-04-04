import pathlib
import sys
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from price_engine_financing_carry import build_financing_carry  # noqa: E402


class PriceEngineFinancingCarryTests(unittest.TestCase):
    def test_interest_only_carry_is_monthly_interest_only(self) -> None:
        carry = build_financing_carry(
            {"interestOnly": True},
            effective_principal=Decimal("101745"),
            annual_interest_rate=Decimal("0.08"),
            holding_months=12,
            amortization_months=360,
        )

        self.assertEqual(carry.debt_service_type, "interest-only")
        self.assertEqual(carry.monthly_debt_service.quantize(Decimal("0.01")), Decimal("678.30"))
        self.assertEqual(carry.total_interest_carry.quantize(Decimal("0.01")), Decimal("8139.60"))
        self.assertEqual(carry.exit_loan_payoff.quantize(Decimal("0.01")), Decimal("101745.00"))

    def test_amortized_carry_uses_monthly_pi_and_reduces_exit_balance(self) -> None:
        carry = build_financing_carry(
            {"interestOnly": False},
            effective_principal=Decimal("101745"),
            annual_interest_rate=Decimal("0.08"),
            holding_months=12,
            amortization_months=360,
        )

        self.assertEqual(carry.debt_service_type, "amortized")
        self.assertEqual(carry.monthly_debt_service.quantize(Decimal("0.01")), Decimal("746.57"))
        self.assertEqual(carry.total_interest_carry.quantize(Decimal("0.01")), Decimal("8108.88"))
        self.assertEqual(carry.exit_loan_payoff.quantize(Decimal("0.01")), Decimal("100895.06"))


if __name__ == "__main__":
    unittest.main()
