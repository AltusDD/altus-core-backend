from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

_ZERO_MONEY = Decimal("0.00")


@dataclass(frozen=True)
class LibertyQuoteSnapshot:
    quote_reference: str
    snapshot_version: str
    source: str
    export_artifact_id: str | None
    export_artifact_type: str | None
    quoted_at: str | None
    captured_at: str | None
    expires_at: str | None
    title_premium: Decimal
    settlement_fee: Decimal
    recording_fee: Decimal
    owner_policy: Decimal
    lender_policy: Decimal
    endorsements: Decimal
    transfer_taxes: Decimal
    other_fees: Decimal
    warning: str | None


def normalize_liberty_quote_snapshot(provider_context: dict[str, Any]) -> LibertyQuoteSnapshot | None:
    if not isinstance(provider_context, dict):
        return None

    canonical_snapshot = provider_context.get("libertySnapshot")
    if isinstance(canonical_snapshot, dict):
        return _normalize_canonical_snapshot(canonical_snapshot)

    legacy_snapshot = provider_context.get("libertyQuote")
    if isinstance(legacy_snapshot, dict):
        return _normalize_legacy_snapshot(legacy_snapshot)

    return None


def _normalize_canonical_snapshot(snapshot: dict[str, Any]) -> LibertyQuoteSnapshot:
    fees = snapshot.get("fees") or {}
    if not isinstance(fees, dict):
        raise ValueError("libertySnapshot.fees must be an object")

    quote_reference = _required_string(snapshot, "quoteReference")
    snapshot_version = _string_or_default(snapshot.get("snapshotVersion"), "v1")
    source = _string_or_default(snapshot.get("source"), "liberty_iframe_snapshot")

    return LibertyQuoteSnapshot(
        quote_reference=quote_reference,
        snapshot_version=snapshot_version,
        source=source,
        export_artifact_id=_optional_string(snapshot.get("exportArtifactId")),
        export_artifact_type=_optional_string(snapshot.get("exportArtifactType")),
        quoted_at=_optional_string(snapshot.get("quotedAt")),
        captured_at=_optional_string(snapshot.get("capturedAt")),
        expires_at=_optional_string(snapshot.get("expiresAt")),
        title_premium=_decimal_field(fees, "titlePremium"),
        settlement_fee=_decimal_field(fees, "settlementFee", aliases=("settlementServices",)),
        recording_fee=_decimal_field(fees, "recordingFee", aliases=("recordingFees",)),
        owner_policy=_decimal_field(fees, "ownerPolicy"),
        lender_policy=_decimal_field(fees, "lenderPolicy"),
        endorsements=_decimal_field(fees, "endorsements", required=False, default=_ZERO_MONEY),
        transfer_taxes=_decimal_field(fees, "transferTaxes", required=False, default=_ZERO_MONEY),
        other_fees=_decimal_field(fees, "otherFees", required=False, default=_ZERO_MONEY),
        warning=_optional_string(snapshot.get("warning")),
    )


def _normalize_legacy_snapshot(snapshot: dict[str, Any]) -> LibertyQuoteSnapshot:
    quote_reference = _required_string(snapshot, "quoteReference")
    return LibertyQuoteSnapshot(
        quote_reference=quote_reference,
        snapshot_version="legacy-v0",
        source="liberty_iframe_snapshot_legacy",
        export_artifact_id=None,
        export_artifact_type=None,
        quoted_at=None,
        captured_at=None,
        expires_at=_optional_string(snapshot.get("expiresAt")),
        title_premium=_decimal_field(snapshot, "titlePremium"),
        settlement_fee=_decimal_field(snapshot, "settlementFee", aliases=("settlementServices",)),
        recording_fee=_decimal_field(snapshot, "recordingFee", aliases=("recordingFees",)),
        owner_policy=_decimal_field(snapshot, "ownerPolicy"),
        lender_policy=_decimal_field(snapshot, "lenderPolicy"),
        endorsements=_decimal_field(snapshot, "endorsements", required=False, default=_ZERO_MONEY),
        transfer_taxes=_decimal_field(snapshot, "transferTaxes", required=False, default=_ZERO_MONEY),
        other_fees=_decimal_field(snapshot, "otherFees", required=False, default=_ZERO_MONEY),
        warning=_optional_string(snapshot.get("warning")),
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
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} must be numeric") from exc
        if decimal_value < _ZERO_MONEY:
            raise ValueError(f"{field_name} must be non-negative")
        return decimal_value

    if required:
        raise ValueError(f"{field_name} is required")
    return default


def _required_string(payload: dict[str, Any], field_name: str) -> str:
    value = _optional_string(payload.get(field_name))
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _string_or_default(value: Any, default: str) -> str:
    normalized = _optional_string(value)
    return normalized if normalized is not None else default


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("snapshot metadata fields must be strings")
    cleaned = value.strip()
    return cleaned or None
