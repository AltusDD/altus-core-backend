from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from price_engine_errors import PriceEngineError


@dataclass(frozen=True)
class DispositionMetrics:
    gross_sale_proceeds: Decimal
    total_exit_costs: Decimal
    net_disposition_proceeds: Decimal
    exit_loan_payoff: Decimal
    sale_commission_cost: Decimal
    seller_closing_cost: Decimal
    disposition_fee: Decimal
    seller_concessions: Decimal
    other_exit_costs: Decimal


def build_disposition_metrics(
    payload: dict[str, Any],
    *,
    default_sale_price: Decimal,
    exit_loan_payoff: Decimal,
    legacy_selling_costs: Decimal,
) -> DispositionMetrics:
    gross_sale_proceeds = _decimal_field(payload, "exitSalePrice", default=default_sale_price)
    sale_commission_rate = _decimal_field(payload, "saleCommissionRate", default=Decimal("0"))
    seller_closing_cost_rate = _decimal_field(payload, "sellerClosingCostRate", default=Decimal("0"))
    disposition_fee = _decimal_field(payload, "dispositionFee", default=Decimal("0"))
    seller_concessions = _decimal_field(payload, "sellerConcessions", default=Decimal("0"))
    explicit_other_exit_costs = payload.get("otherExitCosts")
    other_exit_costs = _decimal_field(payload, "otherExitCosts", default=legacy_selling_costs if explicit_other_exit_costs is None else Decimal("0"))

    if sale_commission_rate > Decimal("1") or seller_closing_cost_rate > Decimal("1"):
        raise PriceEngineError("VALIDATION_FAILED", "saleCommissionRate and sellerClosingCostRate must be between 0 and 1")

    sale_commission_cost = gross_sale_proceeds * sale_commission_rate
    seller_closing_cost = gross_sale_proceeds * seller_closing_cost_rate
    total_exit_costs = (
        sale_commission_cost
        + seller_closing_cost
        + disposition_fee
        + seller_concessions
        + other_exit_costs
    )
    net_disposition_proceeds = gross_sale_proceeds - total_exit_costs - exit_loan_payoff

    return DispositionMetrics(
        gross_sale_proceeds=gross_sale_proceeds,
        total_exit_costs=total_exit_costs,
        net_disposition_proceeds=net_disposition_proceeds,
        exit_loan_payoff=exit_loan_payoff,
        sale_commission_cost=sale_commission_cost,
        seller_closing_cost=seller_closing_cost,
        disposition_fee=disposition_fee,
        seller_concessions=seller_concessions,
        other_exit_costs=other_exit_costs,
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
