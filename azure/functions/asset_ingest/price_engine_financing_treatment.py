from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from price_engine_errors import PriceEngineError


@dataclass(frozen=True)
class FinancingTreatment:
    total_points: Decimal
    cash_paid_points: Decimal
    financed_points: Decimal
    cash_paid_lender_fees: Decimal
    financed_lender_fees: Decimal
    cash_paid_title_fees: Decimal
    financed_title_fees: Decimal
    cash_paid_transaction_costs: Decimal
    financed_transaction_costs: Decimal
    effective_loan_payoff: Decimal
    finance_lender_fees: bool
    finance_title_fees: bool
    finance_points: bool


def build_financing_treatment(
    payload: dict[str, Any],
    *,
    loan_amount: Decimal,
    total_lender_fees: Decimal,
    total_title_fees: Decimal,
    explicit_points: Decimal,
) -> FinancingTreatment:
    points_rate = _decimal_field(payload, "pointsRate", default=Decimal("0"))
    total_points = (loan_amount * points_rate) if points_rate > Decimal("0") else explicit_points

    finance_lender_fees = _bool_field(payload, "financeLenderFees", default=False)
    finance_title_fees = _bool_field(payload, "financeTitleFees", default=False)
    finance_points = _bool_field(payload, "financePoints", default=False)

    financed_lender_fees = total_lender_fees if finance_lender_fees else Decimal("0")
    financed_title_fees = total_title_fees if finance_title_fees else Decimal("0")
    financed_points = total_points if finance_points else Decimal("0")

    cash_paid_lender_fees = total_lender_fees - financed_lender_fees
    cash_paid_title_fees = total_title_fees - financed_title_fees
    cash_paid_points = total_points - financed_points

    financed_transaction_costs = financed_lender_fees + financed_title_fees + financed_points
    cash_paid_transaction_costs = cash_paid_lender_fees + cash_paid_title_fees + cash_paid_points

    return FinancingTreatment(
        total_points=total_points,
        cash_paid_points=cash_paid_points,
        financed_points=financed_points,
        cash_paid_lender_fees=cash_paid_lender_fees,
        financed_lender_fees=financed_lender_fees,
        cash_paid_title_fees=cash_paid_title_fees,
        financed_title_fees=financed_title_fees,
        cash_paid_transaction_costs=cash_paid_transaction_costs,
        financed_transaction_costs=financed_transaction_costs,
        effective_loan_payoff=loan_amount + financed_transaction_costs,
        finance_lender_fees=finance_lender_fees,
        finance_title_fees=finance_title_fees,
        finance_points=finance_points,
    )


def _decimal_field(payload: dict[str, Any], field_name: str, *, default: Decimal) -> Decimal:
    value = payload.get(field_name)
    if value is None:
        return default
    try:
        parsed = Decimal(str(value))
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be numeric") from exc
    if parsed < Decimal("0"):
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be non-negative")
    return parsed


def _bool_field(payload: dict[str, Any], field_name: str, *, default: bool) -> bool:
    value = payload.get(field_name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be a boolean")
