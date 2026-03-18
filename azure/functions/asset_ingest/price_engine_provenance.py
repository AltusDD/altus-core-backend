from __future__ import annotations

from datetime import datetime
from typing import Any

from price_engine_title_quote_context import PriceEngineTitleQuoteContext


def build_price_engine_provenance(
    *,
    title_quote_context: PriceEngineTitleQuoteContext,
    scenario_profile: str,
    applied_preset_fields: list[str],
    validation_warnings: list[str],
) -> dict[str, Any]:
    provider = title_quote_context.provider_key or "none"
    status = title_quote_context.status or "not_requested"
    source = (
        str(title_quote_context.provider_context.get("source") or "").strip()
        or _source_from_status(status)
    )
    source_warnings = list(title_quote_context.warnings)
    source_warning_codes = _build_source_warning_codes(
        provider=provider,
        status=status,
        source=source,
        snapshot_version=_string_or_none(title_quote_context.provider_context.get("snapshotVersion")),
        expires_at=title_quote_context.expires_at,
        quoted_at=_string_or_none(title_quote_context.provider_context.get("quotedAt")),
        captured_at=_string_or_none(title_quote_context.provider_context.get("capturedAt")),
        warnings=source_warnings,
    )
    source_warning_severities = [
        _warning_code_severity(code)
        for code in source_warning_codes
    ]
    warning_summary = _build_warning_summary(source_warning_severities)
    warning_counts = _build_warning_counts(source_warning_severities)
    export_artifact_id = _string_or_none(title_quote_context.provider_context.get("exportArtifactId"))
    export_artifact_type = _string_or_none(title_quote_context.provider_context.get("exportArtifactType"))
    quote_reference = title_quote_context.quote_reference
    snapshot_version = _string_or_none(title_quote_context.provider_context.get("snapshotVersion"))
    source_trace_key = _build_source_trace_key(
        provider=provider,
        status=status,
        source=source,
    )
    snapshot_trace_key = _build_snapshot_trace_key(
        provider=provider,
        snapshot_version=snapshot_version,
        quote_reference=quote_reference,
    )

    return {
        "titleQuote": {
            "provider": provider,
            "status": status,
            "source": source,
            "quoteReference": quote_reference,
            "snapshotVersion": snapshot_version,
            "quotedAt": _string_or_none(title_quote_context.provider_context.get("quotedAt")),
            "capturedAt": _string_or_none(title_quote_context.provider_context.get("capturedAt")),
            "expiresAt": title_quote_context.expires_at,
            "sourceWarnings": source_warnings,
            "sourceWarningCodes": source_warning_codes,
            "sourceWarningSeverities": source_warning_severities,
            "warningSummary": warning_summary,
            "warningCounts": warning_counts,
            "exportArtifactId": export_artifact_id,
            "exportArtifactType": export_artifact_type,
            "exportTraceKey": _build_export_trace_key(
                provider=provider,
                export_artifact_type=export_artifact_type,
                export_artifact_id=export_artifact_id,
                quote_reference=quote_reference,
            ),
            "sourceTraceKey": source_trace_key,
            "snapshotTraceKey": snapshot_trace_key,
            "sourceEventRef": _build_event_ref("source-event", source_trace_key),
            "snapshotEventRef": _build_event_ref("snapshot-event", snapshot_trace_key),
        },
        "scenario": {
            "profile": scenario_profile,
            "appliedPresetFields": list(applied_preset_fields),
            "validationWarnings": list(validation_warnings),
        },
        "trace": {
            "generatedAt": None,
        },
    }


def _source_from_status(status: str) -> str:
    if status in {"stub", "fallback_stub"}:
        return "stub"
    if status == "quoted":
        return "provider_quote"
    return "not_requested"


def _build_source_warning_codes(
    *,
    provider: str,
    status: str,
    source: str,
    snapshot_version: str | None,
    expires_at: str | None,
    quoted_at: str | None,
    captured_at: str | None,
    warnings: list[str],
) -> list[str]:
    codes: list[str] = []

    if provider == "stub":
        codes.append("stub_provider_used")

    if status == "fallback_stub":
        codes.append("fallback_stub_used")

    normalized_warnings = [warning.lower() for warning in warnings]

    if source == "liberty_iframe_snapshot" and any(
        "tokenized app launch rather than a documented backend quote api" in warning
        for warning in normalized_warnings
    ):
        codes.append("liberty_iframe_no_backend_api")

    if any("incomplete or invalid" in warning for warning in normalized_warnings):
        codes.append("snapshot_missing_required_fields")

    if any("no approved liberty snapshot was provided" in warning for warning in normalized_warnings):
        codes.append("quote_source_unavailable")

    if snapshot_version == "legacy-v0":
        codes.append("legacy_quote_alias_normalized")

    if _is_expired(expires_at=expires_at, quoted_at=quoted_at, captured_at=captured_at):
        codes.append("snapshot_expired")

    return codes


def _build_export_trace_key(
    *,
    provider: str,
    export_artifact_type: str | None,
    export_artifact_id: str | None,
    quote_reference: str | None,
) -> str | None:
    if export_artifact_type and export_artifact_id:
        return f"{provider}:{export_artifact_type}:{export_artifact_id}"
    if quote_reference:
        return f"{provider}:quote:{quote_reference}"
    return None


def _warning_code_severity(code: str) -> str:
    if code in {"snapshot_missing_required_fields", "snapshot_expired", "quote_source_unavailable"}:
        return "critical"
    if code in {"fallback_stub_used", "liberty_iframe_no_backend_api"}:
        return "warning"
    return "info"


def _build_warning_summary(severities: list[str]) -> dict[str, Any]:
    highest_severity = None
    if "critical" in severities:
        highest_severity = "critical"
    elif "warning" in severities:
        highest_severity = "warning"
    elif "info" in severities:
        highest_severity = "info"

    return {
        "highestSeverity": highest_severity,
        "hasCritical": "critical" in severities,
        "hasWarning": "warning" in severities,
        "hasInfo": "info" in severities,
    }


def _build_warning_counts(severities: list[str]) -> dict[str, int]:
    return {
        "critical": severities.count("critical"),
        "warning": severities.count("warning"),
        "info": severities.count("info"),
        "total": len(severities),
    }


def _build_event_ref(prefix: str, trace_key: str | None) -> str | None:
    if trace_key is None:
        return None
    return f"{prefix}:{trace_key}"


def _build_source_trace_key(*, provider: str, status: str, source: str) -> str:
    return f"{provider}:{status}:{source}"


def _build_snapshot_trace_key(
    *,
    provider: str,
    snapshot_version: str | None,
    quote_reference: str | None,
) -> str | None:
    if snapshot_version and quote_reference:
        return f"{provider}:{snapshot_version}:{quote_reference}"
    if quote_reference:
        return f"{provider}:snapshot:{quote_reference}"
    return None


def _is_expired(*, expires_at: str | None, quoted_at: str | None, captured_at: str | None) -> bool:
    if expires_at is None:
        return False
    expires_at_value = _parse_iso8601(expires_at)
    if expires_at_value is None:
        return False
    reference_time = _parse_iso8601(captured_at or quoted_at or "")
    if reference_time is None:
        return False
    return expires_at_value <= reference_time


def _parse_iso8601(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None
