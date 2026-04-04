from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from price_engine_errors import PriceEngineError

_PRESET_FIELDS = {
    "flip": {
        "holdingMonths": 6,
        "annualInterestRate": 0.10,
        "interestOnly": True,
        "amortizationMonths": 360,
        "saleCommissionRate": 0.06,
        "sellerClosingCostRate": 0.02,
        "targetProfitMargin": 0.12,
    },
    "brrrr": {
        "holdingMonths": 9,
        "annualInterestRate": 0.085,
        "interestOnly": True,
        "amortizationMonths": 360,
        "saleCommissionRate": 0.06,
        "sellerClosingCostRate": 0.02,
        "targetProfitMargin": 0.10,
    },
    "rental_hold": {
        "holdingMonths": 12,
        "annualInterestRate": 0.075,
        "interestOnly": False,
        "amortizationMonths": 360,
        "saleCommissionRate": 0.06,
        "sellerClosingCostRate": 0.02,
        "targetProfitMargin": 0.08,
    },
}

_NON_NEGATIVE_FIELDS = (
    "purchasePrice",
    "afterRepairValue",
    "exitSalePrice",
    "loanAmount",
    "loanOriginationFee",
    "underwritingFee",
    "processingFee",
    "appraisalFee",
    "creditReportFee",
    "points",
    "closingCosts",
    "holdingCosts",
    "rehabCost",
    "cashAvailable",
    "rentMonthly",
    "operatingExpenseMonthly",
    "dispositionFee",
    "sellerConcessions",
    "otherExitCosts",
    "reserves",
)


@dataclass(frozen=True)
class NormalizedPriceEnginePayload:
    payload: dict[str, Any]
    scenario_profile: str
    applied_preset_fields: list[str]
    validation_warnings: list[str]


def normalize_price_engine_payload(payload: dict[str, Any]) -> NormalizedPriceEnginePayload:
    if not isinstance(payload, dict):
        raise PriceEngineError("VALIDATION_FAILED", "Request body must be an object")

    normalized = dict(payload)
    strategy = str(normalized.get("strategy") or "").strip()
    preset = _PRESET_FIELDS.get(strategy)
    if preset is None:
        if strategy:
            raise PriceEngineError("UNSUPPORTED_STRATEGY_MODE", "strategy must be flip, rental_hold, or brrrr")
        raise PriceEngineError("UNSUPPORTED_STRATEGY_MODE", "strategy must be flip, rental_hold, or brrrr")

    applied_fields: list[str] = []
    for field_name, value in preset.items():
        if normalized.get(field_name) is None:
            normalized[field_name] = value
            applied_fields.append(field_name)

    _validate_non_negative_fields(normalized)
    _validate_rate(normalized, "annualInterestRate", minimum=Decimal("0"), maximum=Decimal("1"))
    _validate_rate(normalized, "interestRateAnnual", minimum=Decimal("0"), maximum=Decimal("1"))
    _validate_rate(normalized, "saleCommissionRate", minimum=Decimal("0"), maximum=Decimal("1"))
    _validate_rate(normalized, "sellerClosingCostRate", minimum=Decimal("0"), maximum=Decimal("1"))
    _validate_rate(normalized, "pointsRate", minimum=Decimal("0"), maximum=Decimal("0.25"))
    _validate_positive_int(normalized, "holdingMonths")
    _validate_positive_int(normalized, "amortizationMonths")

    validation_warnings: list[str] = []
    if applied_fields:
        validation_warnings.append(
            "Scenario preset defaults were applied for missing fields: " + ", ".join(applied_fields) + "."
        )

    return NormalizedPriceEnginePayload(
        payload=normalized,
        scenario_profile=strategy,
        applied_preset_fields=applied_fields,
        validation_warnings=validation_warnings,
    )


def _validate_non_negative_fields(payload: dict[str, Any]) -> None:
    for field_name in _NON_NEGATIVE_FIELDS:
        if payload.get(field_name) is None:
            continue
        value = _decimal_value(payload[field_name], field_name)
        if value < Decimal("0"):
            raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be non-negative")


def _validate_rate(payload: dict[str, Any], field_name: str, *, minimum: Decimal, maximum: Decimal) -> None:
    if payload.get(field_name) is None:
        return
    value = _decimal_value(payload[field_name], field_name)
    if value < minimum or value > maximum:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be between {minimum} and {maximum}")


def _validate_positive_int(payload: dict[str, Any], field_name: str) -> None:
    if payload.get(field_name) is None:
        return
    try:
        value = int(payload[field_name])
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be an integer") from exc
    if value <= 0:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be greater than 0")


def _decimal_value(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise PriceEngineError("VALIDATION_FAILED", f"{field_name} must be numeric") from exc
