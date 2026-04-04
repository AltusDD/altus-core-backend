from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from price_engine_calculations import DealInputs
from title_rate_provider import (
    StubTitleRateProvider,
    TitleRateProviderError,
    parse_title_rate_quote_request,
    resolve_title_rate_provider,
    serialize_title_rate_quote_result,
)

_ZERO_MONEY = Decimal("0")
_FALLBACK_TITLE_FEES = {
    "titlePremium": 0.0,
    "settlementFee": 0.0,
    "recordingFee": 0.0,
    "ownerPolicy": 0.0,
    "lenderPolicy": 0.0,
}


def enrich_payload_with_title_quote(payload: dict[str, Any], inputs: DealInputs) -> dict[str, Any]:
    title_fee_inputs = resolve_title_fee_inputs(payload, inputs)
    enriched = dict(payload)
    enriched.update(title_fee_inputs)
    return enriched


def resolve_title_fee_inputs(payload: dict[str, Any], inputs: DealInputs) -> dict[str, float]:
    request_payload = build_title_quote_request_payload(payload, inputs)
    if request_payload is None:
        return dict(_FALLBACK_TITLE_FEES)

    request = parse_title_rate_quote_request(request_payload)

    try:
        provider = resolve_title_rate_provider()
        result = provider.quote(request)
    except TitleRateProviderError as exc:
        if exc.code not in {"TITLE_RATE_PROVIDER_NOT_CONFIGURED", "UNSUPPORTED_TITLE_RATE_PROVIDER"}:
            raise
        result = StubTitleRateProvider().quote(request)

    return map_title_quote_to_calculation_inputs(serialize_title_rate_quote_result(result))


def build_title_quote_request_payload(payload: dict[str, Any], inputs: DealInputs) -> dict[str, Any] | None:
    property_state = _optional_string(payload, "propertyState") or _optional_string(payload, "state")
    if property_state is None:
        return None

    return {
        "transactionType": _optional_string(payload, "transactionType") or "purchase",
        "propertyState": property_state,
        "county": _optional_string(payload, "county"),
        "city": _optional_string(payload, "city"),
        "postalCode": _optional_string(payload, "postalCode"),
        "salesPrice": float(inputs.purchase_price),
        "loanAmount": float(inputs.loan_amount),
        "ownerPolicyAmount": float(_decimal_or_default(payload.get("ownerPolicyAmount"), inputs.purchase_price)),
        "lenderPolicyAmount": float(_decimal_or_default(payload.get("lenderPolicyAmount"), inputs.loan_amount)),
        "endorsements": _endorsements(payload.get("endorsements")),
        "transactionDate": _optional_string(payload, "transactionDate"),
        "providerContext": _provider_context(payload.get("providerContext")),
    }


def map_title_quote_to_calculation_inputs(quote: dict[str, Any]) -> dict[str, float]:
    totals = quote.get("totals") or {}
    owner_policy = _decimal_from_quote_total(totals.get("ownerPolicy"))
    lender_policy = _decimal_from_quote_total(totals.get("lenderPolicy"))
    settlement_fee = _decimal_from_quote_total(totals.get("settlementServices"))
    recording_fee = _decimal_from_quote_total(totals.get("recordingFees"))
    total = _decimal_from_quote_total(totals.get("total"))

    title_premium = max(
        _ZERO_MONEY,
        total - owner_policy - lender_policy - settlement_fee - recording_fee,
    )

    return {
        "titlePremium": float(title_premium),
        "settlementFee": float(settlement_fee),
        "recordingFee": float(recording_fee),
        "ownerPolicy": float(owner_policy),
        "lenderPolicy": float(lender_policy),
    }


def _decimal_from_quote_total(value: Any) -> Decimal:
    if value is None:
        return _ZERO_MONEY
    return Decimal(str(value))


def _decimal_or_default(value: Any, default: Decimal) -> Decimal:
    if value is None:
        return default
    return Decimal(str(value))


def _optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _endorsements(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _provider_context(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}
