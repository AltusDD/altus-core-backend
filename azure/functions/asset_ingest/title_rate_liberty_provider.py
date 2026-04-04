from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from title_rate_liberty_snapshot import normalize_liberty_quote_snapshot
from title_rate_provider import (
    TitleRateLineItem,
    TitleRateQuoteRequest,
    TitleRateQuoteResult,
)

_ZERO_MONEY = Decimal("0.00")


class LibertyTitleRateProvider:
    provider_key = "liberty"

    def quote(self, request: TitleRateQuoteRequest) -> TitleRateQuoteResult:
        try:
            snapshot = normalize_liberty_quote_snapshot(request.provider_context)
        except ValueError:
            return self._fallback_result(
                request,
                "Liberty quote retrieval is unavailable because the supplied quote snapshot is incomplete or invalid.",
            )

        if snapshot is None:
            return self._fallback_result(
                request,
                "Liberty quote retrieval is unavailable because no approved Liberty snapshot was provided to the ingest path.",
            )

        total = (
            snapshot.title_premium
            + snapshot.settlement_fee
            + snapshot.recording_fee
            + snapshot.owner_policy
            + snapshot.lender_policy
            + snapshot.endorsements
            + snapshot.transfer_taxes
            + snapshot.other_fees
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return TitleRateQuoteResult(
            provider_key=self.provider_key,
            status="quoted",
            quote_reference=snapshot.quote_reference,
            totals={
                "ownerPolicy": snapshot.owner_policy,
                "lenderPolicy": snapshot.lender_policy,
                "endorsements": snapshot.endorsements,
                "settlementServices": snapshot.settlement_fee,
                "recordingFees": snapshot.recording_fee,
                "transferTaxes": snapshot.transfer_taxes,
                "otherFees": snapshot.other_fees + snapshot.title_premium,
                "total": total,
            },
            line_items=(
                _line_item("title-premium", "policy", "Liberty title premium", snapshot.title_premium),
                _line_item("owner-policy", "policy", "Liberty owner policy", snapshot.owner_policy),
                _line_item("lender-policy", "policy", "Liberty lender policy", snapshot.lender_policy),
                _line_item("settlement-fee", "closing", "Liberty settlement fee", snapshot.settlement_fee),
                _line_item("recording-fee", "government", "Liberty recording fee", snapshot.recording_fee),
            ),
            assumptions=(
                "Liberty quote values were supplied through the approved quote snapshot ingest path.",
                "This build does not place orders and uses quote-only behavior.",
            ),
            warnings=tuple(
                warning
                for warning in (
                    "Liberty public iframe currently exposes a tokenized app launch rather than a documented backend quote API.",
                    snapshot.warning,
                )
                if warning
            ),
            expires_at=snapshot.expires_at,
            provider_context={
                "mode": "snapshot_ingest",
                "requestedProvider": request.provider_context.get("requestedProvider"),
                "source": snapshot.source,
                "snapshotVersion": snapshot.snapshot_version,
                "quotedAt": snapshot.quoted_at,
                "capturedAt": snapshot.captured_at,
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
def _line_item(code: str, category: str, description: str, amount: Decimal) -> TitleRateLineItem:
    return TitleRateLineItem(
        code=code,
        category=category,
        description=description,
        amount=amount,
    )

