from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

_ALLOWED_STRATEGIES = {"flip", "rental_hold", "brrrr"}
_STRATEGY_LEVERAGE = {
    "flip": Decimal("0.80"),
    "rental_hold": Decimal("0.75"),
    "brrrr": Decimal("0.70"),
}


class PriceEngineError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def calculate_price_engine(payload: dict[str, Any]) -> dict[str, Any]:
    strategy = payload.get("strategy")
    if strategy not in _ALLOWED_STRATEGIES:
        raise PriceEngineError("UNSUPPORTED_STRATEGY_MODE", "strategy must be flip, rental_hold, or brrrr")

    purchase_price = _decimal_field(payload, "purchasePrice")
    after_repair_value = _decimal_field(payload, "afterRepairValue")
    rehab_cost = _decimal_field(payload, "rehabCost")
    holding_costs = _decimal_field(payload, "holdingCosts")
    closing_costs = _decimal_field(payload, "closingCosts")
    cash_available = _decimal_field(payload, "cashAvailable")
    rent_monthly = _decimal_field(payload, "rentMonthly", required=False)
    operating_expense_monthly = _decimal_field(payload, "operatingExpenseMonthly", required=False)
    target_profit_margin = _decimal_field(payload, "targetProfitMargin", required=False, default=Decimal("0.10"))

    if min(purchase_price, after_repair_value, rehab_cost, holding_costs, closing_costs, cash_available) < Decimal("0"):
        raise PriceEngineError("VALIDATION_FAILED", "numeric inputs must be non-negative")

    if target_profit_margin < Decimal("0") or target_profit_margin > Decimal("1"):
        raise PriceEngineError("VALIDATION_FAILED", "targetProfitMargin must be between 0 and 1")

    resale_cost_rate = Decimal("0.08")
    financed_amount = purchase_price * _STRATEGY_LEVERAGE[strategy]
    total_project_cost = purchase_price + rehab_cost + holding_costs + closing_costs
    net_sale_proceeds = after_repair_value * (Decimal("1") - resale_cost_rate)
    target_profit = after_repair_value * target_profit_margin
    mao = net_sale_proceeds - rehab_cost - holding_costs - closing_costs - target_profit

    if mao <= Decimal("0"):
        raise PriceEngineError("UNSOLVABLE_MAO", "calculated MAO is not positive")

    cash_to_close = total_project_cost - financed_amount
    monthly_cash_flow = rent_monthly - operating_expense_monthly
    annual_cash_flow = monthly_cash_flow * Decimal("12")
    profit = net_sale_proceeds - total_project_cost

    if cash_to_close <= Decimal("0"):
        raise PriceEngineError("CALCULATION_FAILED", "cash to close must be positive")

    irr = ((profit + annual_cash_flow) / cash_to_close) * Decimal("100")
    coc = (annual_cash_flow / cash_to_close) * Decimal("100")
    liquidity_gap = max(Decimal("0"), cash_to_close - cash_available)
    risk_score = Decimal("45")
    risk_score += Decimal("20") if strategy == "flip" else Decimal("10")
    risk_score += (liquidity_gap / Decimal("10000"))
    risk_score += max(Decimal("0"), Decimal("12") - annual_cash_flow / Decimal("1000"))

    return {
        "MAO": _round_currency(mao),
        "IRR": _round_percent(irr),
        "CoC": _round_percent(coc),
        "CashToClose": _round_currency(cash_to_close),
        "Profit": _round_currency(profit),
        "RiskScore": _round_integer(min(Decimal("100"), max(Decimal("1"), risk_score))),
    }


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
        return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be numeric") from exc


def _round_currency(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_percent(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _round_integer(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
