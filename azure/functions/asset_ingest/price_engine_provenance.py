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
    warning_families = _build_warning_families(source_warning_codes)
    warning_family_summary = list(warning_families)
    warning_family_summary_label = _build_warning_family_summary_label(warning_family_summary)
    warning_summary = _build_warning_summary(source_warning_severities)
    warning_counts = _build_warning_counts(source_warning_severities)
    warning_family_counts = _build_warning_family_counts(warning_families)
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
    source_event_type = _build_source_event_type(status=status)
    snapshot_event_type = _build_snapshot_event_type(snapshot_trace_key=snapshot_trace_key)
    source_event_ref = _build_event_ref("source-event", source_trace_key)
    snapshot_event_ref = _build_event_ref("snapshot-event", snapshot_trace_key)
    source_event_bundle = _build_source_event_bundle(
        source_event_type=source_event_type,
        source_event_ref=source_event_ref,
        snapshot_event_type=snapshot_event_type,
        snapshot_event_ref=snapshot_event_ref,
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
            "warningFamilies": warning_families,
            "warningFamilySummary": warning_family_summary,
            "warningFamilySummaryLabel": warning_family_summary_label,
            "warningSummary": warning_summary,
            "warningCounts": warning_counts,
            "warningFamilyCounts": warning_family_counts,
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
            "sourceEventType": source_event_type,
            "snapshotEventType": snapshot_event_type,
            "sourceEventRef": source_event_ref,
            "snapshotEventRef": snapshot_event_ref,
            "sourceEventBundle": source_event_bundle,
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


def _build_warning_families(codes: list[str]) -> list[str]:
    families: list[str] = []
    for code in codes:
        family = _warning_code_family(code)
        if family not in families:
            families.append(family)
    return families


def _warning_code_family(code: str) -> str:
    if code in {"stub_provider_used", "liberty_iframe_no_backend_api"}:
        return "provider"
    if code in {"snapshot_missing_required_fields", "snapshot_expired"}:
        return "snapshot"
    if code == "fallback_stub_used":
        return "fallback"
    if code == "legacy_quote_alias_normalized":
        return "compatibility"
    return "availability"


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


def _build_warning_family_summary_label(families: list[str]) -> str | None:
    if not families:
        return None
    return ", ".join(families)


def _build_warning_counts(severities: list[str]) -> dict[str, int]:
    return {
        "critical": severities.count("critical"),
        "warning": severities.count("warning"),
        "info": severities.count("info"),
        "total": len(severities),
    }


def _build_warning_family_counts(families: list[str]) -> dict[str, int]:
    return {
        "provider": families.count("provider"),
        "snapshot": families.count("snapshot"),
        "fallback": families.count("fallback"),
        "compatibility": families.count("compatibility"),
        "availability": families.count("availability"),
    }


def _build_event_ref(prefix: str, trace_key: str | None) -> str | None:
    if trace_key is None:
        return None
    return f"{prefix}:{trace_key}"


def _build_source_event_bundle(
    *,
    source_event_type: str | None,
    source_event_ref: str | None,
    snapshot_event_type: str | None,
    snapshot_event_ref: str | None,
) -> dict[str, Any]:
    normalized_source_event_ref = source_event_ref if source_event_type else None
    normalized_snapshot_event_ref = snapshot_event_ref if snapshot_event_type else None
    has_source_event = _has_event(source_event_type, normalized_source_event_ref)
    has_snapshot_event = _has_event(snapshot_event_type, normalized_snapshot_event_ref)
    is_complete = has_source_event and has_snapshot_event
    status = _build_event_bundle_status(
        has_source_event=has_source_event,
        has_snapshot_event=has_snapshot_event,
    )

    return {
        "sourceEventType": source_event_type,
        "sourceEventRef": normalized_source_event_ref,
        "snapshotEventType": snapshot_event_type,
        "snapshotEventRef": normalized_snapshot_event_ref,
        "status": status,
        "statusLabel": _build_event_bundle_status_label(status),
        "hasSourceEvent": has_source_event,
        "hasSnapshotEvent": has_snapshot_event,
        "isComplete": is_complete,
    }


def _has_event(event_type: str | None, event_ref: str | None) -> bool:
    return bool(event_type and event_type.strip() and event_ref and event_ref.strip())


def _build_event_bundle_status(*, has_source_event: bool, has_snapshot_event: bool) -> str:
    if has_source_event and has_snapshot_event:
        return "complete"
    if has_source_event or has_snapshot_event:
        return "partial"
    return "missing"


def _build_event_bundle_status_label(status: str) -> str:
    if status == "complete":
        return "Complete Event Bundle"
    if status == "partial":
        return "Partial Event Bundle"
    return "Missing Event Bundle"


def _build_source_event_type(*, status: str) -> str | None:
    if status == "quoted":
        return "title_quote_source"
    if status == "fallback_stub":
        return "title_quote_fallback"
    if status == "stub":
        return "title_quote_stub"
    if status == "not_requested":
        return None
    return "title_quote_status"


def _build_snapshot_event_type(*, snapshot_trace_key: str | None) -> str | None:
    if snapshot_trace_key is None:
        return None
    return "title_quote_snapshot"


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
