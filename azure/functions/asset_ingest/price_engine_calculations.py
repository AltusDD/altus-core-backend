from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

_ALLOWED_STRATEGIES = {"flip", "rental_hold", "brrrr"}
_DEFAULT_LTV = {
    "flip": Decimal("0.80"),
    "rental_hold": Decimal("0.75"),
    "brrrr": Decimal("0.70"),
}
_DEFAULT_SELLING_COST_RATE = Decimal("0.08")


class PriceEngineError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass(frozen=True)
class DealInputs:
    strategy: str
    purchase_price: Decimal
    after_repair_value: Decimal
    rehab_cost: Decimal
    holding_costs: Decimal
    closing_costs: Decimal
    cash_available: Decimal
    rent_monthly: Decimal
    operating_expense_monthly: Decimal
    selling_costs: Decimal
    reserves: Decimal
    points: Decimal
    loan_amount: Decimal
    financed_ltv: Decimal
    holding_months: int
    interest_rate_annual: Decimal
    amortization_months: int
    target_profit_margin: Decimal


def calculate_price_engine(payload: dict[str, Any]) -> dict[str, Any]:
    inputs = build_deal_inputs(payload)
    return calculate_price_engine_from_inputs(inputs)


def calculate_price_engine_from_inputs(inputs: DealInputs) -> dict[str, Any]:
    mao = calculate_mao(inputs)
    if mao <= Decimal("0"):
        raise PriceEngineError("UNSOLVABLE_MAO", "calculated MAO is not positive")

    cash_to_close = calculate_cash_to_close(inputs)
    if cash_to_close <= Decimal("0"):
        raise PriceEngineError("CALCULATION_FAILED", "cash to close must be positive")

    irr = calculate_irr(inputs, cash_to_close)
    cash_on_cash = calculate_cash_on_cash(inputs, cash_to_close)
    profit = calculate_profit(inputs)
    risk_score = calculate_risk_score(inputs, cash_to_close)

    return {
        "MAO": _round_currency(mao),
        "IRR": _round_percent(irr),
        "CoC": _round_percent(cash_on_cash),
        "CashToClose": _round_currency(cash_to_close),
        "Profit": _round_currency(profit),
        "RiskScore": _round_integer(Decimal(risk_score)),
    }


def build_deal_inputs(payload: dict[str, Any]) -> DealInputs:
    strategy = payload.get("strategy")
    if strategy not in _ALLOWED_STRATEGIES:
        raise PriceEngineError("UNSUPPORTED_STRATEGY_MODE", "strategy must be flip, rental_hold, or brrrr")

    purchase_price = _decimal_field(payload, "purchasePrice")
    after_repair_value = _decimal_field(payload, "afterRepairValue")
    rehab_cost = _decimal_field(payload, "rehabCost")
    holding_costs = _decimal_field(payload, "holdingCosts")
    closing_costs = _decimal_field(payload, "closingCosts")
    cash_available = _decimal_field(payload, "cashAvailable")
    rent_monthly = _decimal_field(payload, "rentMonthly", required=False, default=Decimal("0"))
    operating_expense_monthly = _decimal_field(payload, "operatingExpenseMonthly", required=False, default=Decimal("0"))
    default_selling_costs = after_repair_value * _DEFAULT_SELLING_COST_RATE
    selling_costs = _decimal_field(payload, "sellingCosts", required=False, default=default_selling_costs)
    reserves = _decimal_field(payload, "reserves", required=False, default=Decimal("0"))
    holding_months = _int_field(payload, "holdingMonths", default=12, minimum=1)
    financed_ltv = _decimal_field(payload, "financedLtv", required=False, default=_DEFAULT_LTV[strategy])
    if financed_ltv < Decimal("0") or financed_ltv > Decimal("1"):
        raise PriceEngineError("VALIDATION_FAILED", "financedLtv must be between 0 and 1")

    implied_loan_amount = purchase_price * financed_ltv
    loan_amount = _decimal_field(payload, "loanAmount", required=False, default=implied_loan_amount)
    points = _decimal_field(payload, "points", required=False, default=Decimal("0"))
    points_rate = _decimal_field(payload, "pointsRate", required=False, default=Decimal("0"))
    if points == Decimal("0") and points_rate > Decimal("0"):
        points = loan_amount * points_rate

    interest_rate_annual = _decimal_field(payload, "interestRateAnnual", required=False, default=Decimal("0.08"))
    amortization_months = _int_field(payload, "amortizationMonths", default=360, minimum=1)
    target_profit_margin = _decimal_field(payload, "targetProfitMargin", required=False, default=Decimal("0.10"))

    numeric_fields = (
        purchase_price,
        after_repair_value,
        rehab_cost,
        holding_costs,
        closing_costs,
        cash_available,
        rent_monthly,
        operating_expense_monthly,
        selling_costs,
        reserves,
        points,
        loan_amount,
        interest_rate_annual,
        target_profit_margin,
    )
    if min(numeric_fields) < Decimal("0"):
        raise PriceEngineError("VALIDATION_FAILED", "numeric inputs must be non-negative")

    if loan_amount > purchase_price:
        raise PriceEngineError("VALIDATION_FAILED", "loanAmount cannot exceed purchasePrice")

    return DealInputs(
        strategy=strategy,
        purchase_price=purchase_price,
        after_repair_value=after_repair_value,
        rehab_cost=rehab_cost,
        holding_costs=holding_costs,
        closing_costs=closing_costs,
        cash_available=cash_available,
        rent_monthly=rent_monthly,
        operating_expense_monthly=operating_expense_monthly,
        selling_costs=selling_costs,
        reserves=reserves,
        points=points,
        loan_amount=loan_amount,
        financed_ltv=financed_ltv,
        holding_months=holding_months,
        interest_rate_annual=interest_rate_annual,
        amortization_months=amortization_months,
        target_profit_margin=target_profit_margin,
    )


def calculate_mao(inputs: DealInputs) -> Decimal:
    net_sale_proceeds = inputs.after_repair_value - inputs.selling_costs
    target_profit = inputs.after_repair_value * inputs.target_profit_margin
    return net_sale_proceeds - inputs.rehab_cost - inputs.holding_costs - inputs.closing_costs - target_profit


def calculate_cash_to_close(inputs: DealInputs) -> Decimal:
    down_payment = max(inputs.purchase_price - inputs.loan_amount, Decimal("0"))
    return down_payment + inputs.rehab_cost + inputs.closing_costs + inputs.reserves + inputs.points


def calculate_cash_on_cash(inputs: DealInputs, cash_to_close: Decimal | None = None) -> Decimal:
    effective_cash_to_close = cash_to_close if cash_to_close is not None else calculate_cash_to_close(inputs)
    annual_income = (inputs.rent_monthly - inputs.operating_expense_monthly) * Decimal("12")
    return (annual_income / effective_cash_to_close) * Decimal("100")


def calculate_irr(inputs: DealInputs, cash_to_close: Decimal | None = None) -> Decimal:
    effective_cash_to_close = cash_to_close if cash_to_close is not None else calculate_cash_to_close(inputs)
    monthly_income = inputs.rent_monthly - inputs.operating_expense_monthly
    terminal_value = inputs.after_repair_value - inputs.selling_costs - inputs.loan_amount
    cashflows = (
        [-effective_cash_to_close]
        + [monthly_income for _ in range(max(inputs.holding_months - 1, 0))]
        + [monthly_income + terminal_value]
    )
    return _annualized_irr(cashflows)


def calculate_profit(inputs: DealInputs) -> Decimal:
    return (
        inputs.after_repair_value
        - inputs.selling_costs
        - inputs.purchase_price
        - inputs.rehab_cost
        - inputs.holding_costs
        - inputs.closing_costs
    )


def calculate_risk_score(inputs: DealInputs, cash_to_close: Decimal | None = None) -> int:
    effective_cash_to_close = cash_to_close if cash_to_close is not None else calculate_cash_to_close(inputs)
    annual_cash_flow = (inputs.rent_monthly - inputs.operating_expense_monthly) * Decimal("12")
    liquidity_gap = max(Decimal("0"), effective_cash_to_close - inputs.cash_available)
    risk_score = Decimal("45")
    risk_score += Decimal("20") if inputs.strategy == "flip" else Decimal("10")
    risk_score += liquidity_gap / Decimal("10000")
    risk_score += max(Decimal("0"), Decimal("12") - (annual_cash_flow / Decimal("1000")))
    bounded = min(Decimal("100"), max(Decimal("1"), risk_score))
    return _round_integer(bounded)


def _annualized_irr(cashflows: list[Decimal]) -> Decimal:
    def npv(rate: Decimal) -> Decimal:
        total = Decimal("0")
        for index, cashflow in enumerate(cashflows):
            total += cashflow / ((Decimal("1") + rate) ** index)
        return total

    low = Decimal("-0.9999")
    high = Decimal("10")
    low_npv = npv(low)
    high_npv = npv(high)

    if low_npv == 0:
        monthly_rate = low
    elif high_npv == 0:
        monthly_rate = high
    elif low_npv * high_npv > 0:
        monthly_rate = Decimal("0")
    else:
        monthly_rate = Decimal("0")
        for _ in range(200):
            monthly_rate = (low + high) / Decimal("2")
            mid_npv = npv(monthly_rate)
            if abs(mid_npv) < Decimal("0.0000001"):
                break
            if low_npv * mid_npv <= 0:
                high = monthly_rate
                high_npv = mid_npv
            else:
                low = monthly_rate
                low_npv = mid_npv

    annual_rate = ((Decimal("1") + monthly_rate) ** Decimal("12")) - Decimal("1")
    return annual_rate * Decimal("100")


def _decimal_field(
    payload: dict[str, Any],
    field_name: str,
    *,
    required: bool = True,
    default: Decimal | None = None,
) -> Decimal:
    value = payload.get(field_name)
    if value is None:
        if required:
            raise PriceEngineError("VALIDATION_FAILED", f"{field_name} is required")
        return default if default is not None else Decimal("0")

    try:
        return Decimal(str(value))
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be numeric") from exc


def _int_field(payload: dict[str, Any], field_name: str, *, default: int, minimum: int) -> int:
    value = payload.get(field_name)
    if value is None:
        return default

    try:
        parsed = int(value)
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be an integer") from exc

    if parsed < minimum:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be at least {minimum}")
    return parsed


def _round_currency(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_percent(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_integer(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
