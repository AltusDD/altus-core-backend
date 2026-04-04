from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from title_rate_provider import (
    TitleRateLineItem,
    TitleRateQuoteRequest,
    TitleRateQuoteResult,
)

_ZERO_MONEY = Decimal("0.00")


class LibertyTitleRateProvider:
    provider_key = "liberty"

    def quote(self, request: TitleRateQuoteRequest) -> TitleRateQuoteResult:
        quote = request.provider_context.get("libertyQuote")
        if not isinstance(quote, dict):
            return self._fallback_result(
                request,
                "Liberty quote retrieval is unavailable because this build has no documented server-to-server Liberty quote bridge.",
            )

        try:
            title_premium = _decimal_field(quote, "titlePremium")
            settlement_fee = _decimal_field(quote, "settlementFee", aliases=("settlementServices",))
            recording_fee = _decimal_field(quote, "recordingFee", aliases=("recordingFees",))
            owner_policy = _decimal_field(quote, "ownerPolicy")
            lender_policy = _decimal_field(quote, "lenderPolicy")
            endorsements = _decimal_field(quote, "endorsements", required=False, default=_ZERO_MONEY)
            transfer_taxes = _decimal_field(quote, "transferTaxes", required=False, default=_ZERO_MONEY)
            other_fees = _decimal_field(quote, "otherFees", required=False, default=_ZERO_MONEY)
        except ValueError:
            return self._fallback_result(
                request,
                "Liberty quote retrieval is unavailable because the supplied quote snapshot is incomplete or invalid.",
            )

        total = (
            title_premium
            + settlement_fee
            + recording_fee
            + owner_policy
            + lender_policy
            + endorsements
            + transfer_taxes
            + other_fees
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return TitleRateQuoteResult(
            provider_key=self.provider_key,
            status="quoted",
            quote_reference=_optional_string(quote.get("quoteReference")),
            totals={
                "ownerPolicy": owner_policy,
                "lenderPolicy": lender_policy,
                "endorsements": endorsements,
                "settlementServices": settlement_fee,
                "recordingFees": recording_fee,
                "transferTaxes": transfer_taxes,
                "otherFees": other_fees + title_premium,
                "total": total,
            },
            line_items=(
                _line_item("title-premium", "policy", "Liberty title premium", title_premium),
                _line_item("owner-policy", "policy", "Liberty owner policy", owner_policy),
                _line_item("lender-policy", "policy", "Liberty lender policy", lender_policy),
                _line_item("settlement-fee", "closing", "Liberty settlement fee", settlement_fee),
                _line_item("recording-fee", "government", "Liberty recording fee", recording_fee),
            ),
            assumptions=(
                "Liberty quote values were supplied through the approved quote snapshot bridge.",
                "This build does not place orders and uses quote-only behavior.",
            ),
            warnings=tuple(
                warning
                for warning in (
                    "Liberty public iframe currently exposes a tokenized app launch rather than a documented backend quote API.",
                    _optional_string(quote.get("warning")),
                )
                if warning
            ),
            expires_at=_optional_string(quote.get("expiresAt")),
            provider_context={
                "mode": "quote_snapshot",
                "requestedProvider": request.provider_context.get("requestedProvider"),
                "source": "liberty_iframe_snapshot",
                "automationAvailable": False,
            },
        )

    def _fallback_result(self, request: TitleRateQuoteRequest, warning: str) -> TitleRateQuoteResult:
        return TitleRateQuoteResult(
            provider_key=self.provider_key,
            status="fallback_stub",
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
            assumptions=(
                "Liberty was selected as the title-rate provider.",
                "Deterministic stub totals were used because no approved Liberty quote snapshot was available.",
            ),
            warnings=(
                warning,
                "No order was placed and no unsupported browser automation or scraping was attempted.",
            ),
            expires_at=None,
            provider_context={
                "mode": "fallback_stub",
                "requestedProvider": request.provider_context.get("requestedProvider"),
                "source": "liberty_iframe_snapshot",
                "automationAvailable": False,
            },
        )


def _decimal_field(
    payload: dict[str, Any],
    field_name: str,
    *,
    aliases: tuple[str, ...] = (),
    required: bool = True,
    default: Decimal = _ZERO_MONEY,
) -> Decimal:
    for candidate in (field_name, *aliases):
        value = payload.get(candidate)
        if value is None:
            continue
        try:
            decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if decimal_value < _ZERO_MONEY:
            raise ValueError(f"{field_name} must be non-negative")
        return decimal_value

    if required:
        raise ValueError(f"{field_name} is required")
    return default


def _line_item(code: str, category: str, description: str, amount: Decimal) -> TitleRateLineItem:
    return TitleRateLineItem(
        code=code,
        category=category,
        description=description,
        amount=amount,
    )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None
