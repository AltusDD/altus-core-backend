from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Protocol


_ALLOWED_TRANSACTION_TYPES = {"purchase", "refinance", "sale"}
_ZERO_MONEY = Decimal("0.00")
_TITLE_RATE_PROVIDER_ENV = "PRICE_ENGINE_TITLE_RATE_PROVIDER"


class TitleRateProviderError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass(frozen=True)
class TitleRateQuoteRequest:
    transaction_type: str
    property_state: str
    sales_price: Decimal
    loan_amount: Decimal
    county: str | None
    city: str | None
    postal_code: str | None
    owner_policy_amount: Decimal
    lender_policy_amount: Decimal
    endorsements: tuple[str, ...]
    transaction_date: str | None
    provider_context: dict[str, Any]


@dataclass(frozen=True)
class TitleRateLineItem:
    code: str
    category: str
    description: str
    amount: Decimal


@dataclass(frozen=True)
class TitleRateQuoteResult:
    provider_key: str
    status: str
    quote_reference: str | None
    totals: dict[str, Decimal]
    line_items: tuple[TitleRateLineItem, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    expires_at: str | None
    provider_context: dict[str, Any]


class TitleRateProvider(Protocol):
    provider_key: str

    def quote(self, request: TitleRateQuoteRequest) -> TitleRateQuoteResult:
        ...


class StubTitleRateProvider:
    provider_key = "stub"

    def quote(self, request: TitleRateQuoteRequest) -> TitleRateQuoteResult:
        assumptions = (
            "No approved title-rate provider is configured for automated quoting yet.",
            f"Normalized request accepted for {request.transaction_type} in {request.property_state}.",
        )
        warnings = (
            "Stub response only. Vendor implementation remains disabled pending an approved API or documented embed bridge.",
        )
        return TitleRateQuoteResult(
            provider_key=self.provider_key,
            status="stub",
            quote_reference=None,
            totals={
                "ownerPolicy": _ZERO_MONEY,
                "lenderPolicy": _ZERO_MONEY,
                "endorsements": _ZERO_MONEY,
                "settlementServices": _ZERO_MONEY,
                "recordingFees": _ZERO_MONEY,
                "transferTaxes": _ZERO_MONEY,
                "otherFees": _ZERO_MONEY,
                "total": _ZERO_MONEY,
            },
            line_items=(),
            assumptions=assumptions,
            warnings=warnings,
            expires_at=None,
            provider_context={"mode": "stub", "requestedProvider": request.provider_context.get("requestedProvider")},
        )


def resolve_title_rate_provider() -> TitleRateProvider:
    provider_key = os.getenv(_TITLE_RATE_PROVIDER_ENV, "").strip().lower()
    if not provider_key:
        raise TitleRateProviderError(
            "TITLE_RATE_PROVIDER_NOT_CONFIGURED",
            "No approved title-rate provider is configured.",
            {"envVar": _TITLE_RATE_PROVIDER_ENV},
        )

    if provider_key == "stub":
        return StubTitleRateProvider()
    if provider_key == "liberty":
        from title_rate_liberty_provider import LibertyTitleRateProvider

        return LibertyTitleRateProvider()

    raise TitleRateProviderError(
        "UNSUPPORTED_TITLE_RATE_PROVIDER",
        "Configured title-rate provider is not supported in this build.",
        {"provider": provider_key},
    )


def parse_title_rate_quote_request(payload: dict[str, Any]) -> TitleRateQuoteRequest:
    transaction_type = str(payload.get("transactionType") or "").strip().lower()
    if transaction_type not in _ALLOWED_TRANSACTION_TYPES:
        raise TitleRateProviderError(
            "VALIDATION_FAILED",
            "transactionType must be purchase, refinance, or sale",
        )

    property_state = str(payload.get("propertyState") or "").strip().upper()
    if len(property_state) != 2 or not property_state.isalpha():
        raise TitleRateProviderError(
            "VALIDATION_FAILED",
            "propertyState must be a 2-letter state code",
        )

    sales_price = _decimal_field(payload, "salesPrice")
    loan_amount = _decimal_field(payload, "loanAmount", required=False, default=_ZERO_MONEY)
    owner_policy_amount = _decimal_field(payload, "ownerPolicyAmount", required=False, default=sales_price)
    lender_policy_amount = _decimal_field(payload, "lenderPolicyAmount", required=False, default=loan_amount)

    if min(sales_price, loan_amount, owner_policy_amount, lender_policy_amount) < Decimal("0"):
        raise TitleRateProviderError("VALIDATION_FAILED", "numeric inputs must be non-negative")

    endorsements_raw = payload.get("endorsements") or []
    if not isinstance(endorsements_raw, list) or any(not isinstance(item, str) or not item.strip() for item in endorsements_raw):
        raise TitleRateProviderError("VALIDATION_FAILED", "endorsements must be an array of non-empty strings")

    provider_context = payload.get("providerContext") or {}
    if not isinstance(provider_context, dict):
        raise TitleRateProviderError("VALIDATION_FAILED", "providerContext must be an object when provided")

    transaction_date = payload.get("transactionDate")
    if transaction_date is not None and not isinstance(transaction_date, str):
        raise TitleRateProviderError("VALIDATION_FAILED", "transactionDate must be a string when provided")

    return TitleRateQuoteRequest(
        transaction_type=transaction_type,
        property_state=property_state,
        sales_price=sales_price,
        loan_amount=loan_amount,
        county=_optional_string(payload, "county"),
        city=_optional_string(payload, "city"),
        postal_code=_optional_string(payload, "postalCode"),
        owner_policy_amount=owner_policy_amount,
        lender_policy_amount=lender_policy_amount,
        endorsements=tuple(item.strip() for item in endorsements_raw),
        transaction_date=transaction_date,
        provider_context=provider_context,
    )


def quote_title_rate(payload: dict[str, Any]) -> dict[str, Any]:
    request = parse_title_rate_quote_request(payload)
    provider = resolve_title_rate_provider()
    result = provider.quote(request)
    return serialize_title_rate_quote_result(result)


def serialize_title_rate_quote_result(result: TitleRateQuoteResult) -> dict[str, Any]:
    return {
        "providerKey": result.provider_key,
        "status": result.status,
        "quoteReference": result.quote_reference,
        "totals": {key: _round_currency(value) for key, value in result.totals.items()},
        "lineItems": [
            {
                "code": item.code,
                "category": item.category,
                "description": item.description,
                "amount": _round_currency(item.amount),
            }
            for item in result.line_items
        ],
        "assumptions": list(result.assumptions),
        "warnings": list(result.warnings),
        "expiresAt": result.expires_at,
        "providerContext": result.provider_context,
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
            raise TitleRateProviderError("VALIDATION_FAILED", f"{field_name} is required")
        return default if default is not None else _ZERO_MONEY

    try:
        return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except Exception as exc:
        raise TitleRateProviderError("VALIDATION_FAILED", f"{field_name} must be numeric") from exc


def _optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TitleRateProviderError("VALIDATION_FAILED", f"{field_name} must be a string when provided")

    cleaned = value.strip()
    return cleaned or None


def _round_currency(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
