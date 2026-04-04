from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from price_engine_errors import PriceEngineError


@dataclass(frozen=True)
class FinancingCarry:
    debt_service_type: str
    monthly_debt_service: Decimal
    total_interest_carry: Decimal
    exit_loan_payoff: Decimal
    interest_only: bool


def build_financing_carry(
    payload: dict[str, Any],
    *,
    effective_principal: Decimal,
    annual_interest_rate: Decimal,
    holding_months: int,
    amortization_months: int,
) -> FinancingCarry:
    interest_only = _bool_field(payload, "interestOnly", default=True)
    monthly_rate = annual_interest_rate / Decimal("12")

    if effective_principal <= Decimal("0"):
        return FinancingCarry(
            debt_service_type="none",
            monthly_debt_service=Decimal("0"),
            total_interest_carry=Decimal("0"),
            exit_loan_payoff=Decimal("0"),
            interest_only=interest_only,
        )

    if interest_only:
        monthly_payment = effective_principal * monthly_rate
        total_interest_carry = monthly_payment * Decimal(holding_months)
        return FinancingCarry(
            debt_service_type="interest-only",
            monthly_debt_service=monthly_payment,
            total_interest_carry=total_interest_carry,
            exit_loan_payoff=effective_principal,
            interest_only=True,
        )

    monthly_payment = _amortized_monthly_payment(effective_principal, monthly_rate, amortization_months)
    remaining_balance = effective_principal
    total_interest_carry = Decimal("0")
    for _ in range(min(holding_months, amortization_months)):
        interest_component = remaining_balance * monthly_rate
        principal_component = monthly_payment - interest_component
        if principal_component < Decimal("0"):
            principal_component = Decimal("0")
        total_interest_carry += interest_component
        remaining_balance = max(Decimal("0"), remaining_balance - principal_component)

    return FinancingCarry(
        debt_service_type="amortized",
        monthly_debt_service=monthly_payment,
        total_interest_carry=total_interest_carry,
        exit_loan_payoff=remaining_balance,
        interest_only=False,
    )


def _amortized_monthly_payment(principal: Decimal, monthly_rate: Decimal, amortization_months: int) -> Decimal:
    if amortization_months <= 0:
        raise PriceEngineError("VALIDATION_FAILED", "amortizationMonths must be at least 1")
    if monthly_rate == Decimal("0"):
        return principal / Decimal(amortization_months)
    numerator = principal * monthly_rate
    denominator = Decimal("1") - ((Decimal("1") + monthly_rate) ** Decimal(-amortization_months))
    if denominator == Decimal("0"):
        raise PriceEngineError("CALCULATION_FAILED", "amortized payment denominator is zero")
    return numerator / denominator


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
