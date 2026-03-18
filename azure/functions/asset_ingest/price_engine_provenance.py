from __future__ import annotations

from datetime import datetime
from typing import Any

from price_engine_corelogic_scaffold import resolve_corelogic_integration_scaffold
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
    warning_family_display_priority = _build_warning_family_display_priority(warning_family_counts)
    warning_family_display_label = _build_warning_family_display_label(warning_family_display_priority)
    warning_family_display_severity = _build_warning_family_display_severity(
        selected_family=warning_family_display_priority,
        warning_codes=source_warning_codes,
        warning_summary=warning_summary,
    )
    warning_family_display_count = _build_warning_family_display_count(
        selected_family=warning_family_display_priority,
        warning_family_counts=warning_family_counts,
    )
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
    corelogic_integration = resolve_corelogic_integration_scaffold(
        title_quote_context.provider_context
    )
    export_trace_key = _build_export_trace_key(
        provider=provider,
        export_artifact_type=export_artifact_type,
        export_artifact_id=export_artifact_id,
        quote_reference=quote_reference,
    )
    export_readiness_reason_codes = _build_export_readiness_reason_codes(
        export_artifact_id=export_artifact_id,
        export_trace_key=export_trace_key,
        quote_reference=quote_reference,
        snapshot_version=snapshot_version,
        source_trace_key=source_trace_key,
        snapshot_trace_key=snapshot_trace_key,
        source_event_bundle=source_event_bundle,
        warning_summary=warning_summary,
        warning_counts=warning_counts,
    )
    export_readiness = _build_export_readiness(export_readiness_reason_codes)
    audit_completeness = _build_audit_completeness(
        source_trace_key=source_trace_key,
        snapshot_trace_key=snapshot_trace_key,
        source_event_bundle=source_event_bundle,
        quote_reference=quote_reference,
        snapshot_version=snapshot_version,
        captured_at=_string_or_none(title_quote_context.provider_context.get("capturedAt")),
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
            "warningFamilyDisplayPriority": warning_family_display_priority,
            "warningFamilyDisplayLabel": warning_family_display_label,
            "warningFamilyDisplaySeverity": warning_family_display_severity,
            "warningFamilyDisplayCount": warning_family_display_count,
            "warningSummary": warning_summary,
            "warningCounts": warning_counts,
            "warningFamilyCounts": warning_family_counts,
            "exportArtifactId": export_artifact_id,
            "exportArtifactType": export_artifact_type,
            "exportTraceKey": export_trace_key,
            "sourceTraceKey": source_trace_key,
            "snapshotTraceKey": snapshot_trace_key,
            "sourceEventType": source_event_type,
            "snapshotEventType": snapshot_event_type,
            "sourceEventRef": source_event_ref,
            "snapshotEventRef": snapshot_event_ref,
            "sourceEventBundle": source_event_bundle,
            "integrationProvider": corelogic_integration.provider,
            "integrationMode": corelogic_integration.mode,
            "integrationState": corelogic_integration.state,
            "integrationStateLabel": corelogic_integration.state_label,
            "integrationReasonCodes": corelogic_integration.reason_codes,
            "integrationLiveReady": corelogic_integration.live_ready,
            "integrationLiveReadyLabel": corelogic_integration.live_ready_label,
            "integrationCredentialState": corelogic_integration.credential_state,
            "integrationCredentialStateLabel": corelogic_integration.credential_state_label,
            "integrationGuardSummary": corelogic_integration.guard_summary,
            "integrationArtifactType": corelogic_integration.artifact_type,
            "integrationArtifactId": corelogic_integration.artifact_id,
            "integrationTraceKey": corelogic_integration.trace_key,
            "integrationEventType": corelogic_integration.event_type,
            "integrationEventRef": corelogic_integration.event_ref,
            "integrationMockProfile": corelogic_integration.mock_profile,
            "integrationMockProfileLabel": corelogic_integration.mock_profile_label,
            "integrationResultType": _integration_bridge_value(
                corelogic_integration.normalized_result,
                "resultType",
            ),
            "integrationExecutionState": _integration_bridge_value(
                corelogic_integration.normalized_result,
                "executionState",
            ),
            "integrationQuoteReference": _integration_bridge_value(
                corelogic_integration.normalized_result,
                "quoteReference",
            ),
            "integrationSnapshotVersion": _integration_bridge_value(
                corelogic_integration.normalized_result,
                "snapshotVersion",
            ),
            "integrationPayloadProfile": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "profile",
            ),
            "integrationEstimatedTotalTitleCost": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedTotalTitleCost",
            ),
            "integrationCurrency": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "currency",
            ),
            "integrationEstimatedTitleFee": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedTitleFee",
            ),
            "integrationEstimatedSettlementFee": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedSettlementFee",
            ),
            "integrationEstimatedRecordingFee": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedRecordingFee",
            ),
            "integrationEstimatedSearchFee": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedSearchFee",
            ),
            "integrationEstimatedMiscFee": _integration_payload_bridge_value(
                corelogic_integration.normalized_result,
                "estimatedMiscFee",
            ),
            "exportReadiness": export_readiness,
            "exportReadinessLabel": _build_export_readiness_label(export_readiness),
            "exportReadinessReasonCodes": export_readiness_reason_codes,
            "auditCompleteness": audit_completeness,
            "auditCompletenessLabel": _build_audit_completeness_label(audit_completeness),
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


def _build_warning_family_display_priority(warning_family_counts: dict[str, int]) -> str | None:
    for family in ("fallback", "availability", "provider", "compatibility", "snapshot"):
        if warning_family_counts.get(family, 0) > 0:
            return family
    return None


def _build_warning_family_display_label(selected_family: str | None) -> str | None:
    if selected_family == "fallback":
        return "Fallback Warning"
    if selected_family == "availability":
        return "Availability Warning"
    if selected_family == "provider":
        return "Provider Warning"
    if selected_family == "compatibility":
        return "Compatibility Warning"
    if selected_family == "snapshot":
        return "Snapshot Warning"
    return None


def _build_warning_family_display_severity(
    *,
    selected_family: str | None,
    warning_codes: list[str],
    warning_summary: dict[str, Any],
) -> str | None:
    if selected_family is None:
        return None

    severities = [
        _warning_code_severity(code)
        for code in warning_codes
        if _warning_code_family(code) == selected_family
    ]
    if severities:
        return _highest_severity(severities)
    return warning_summary.get("highestSeverity")


def _build_warning_family_display_count(
    *,
    selected_family: str | None,
    warning_family_counts: dict[str, int],
) -> int:
    if selected_family is None:
        return 0
    return int(warning_family_counts.get(selected_family, 0))


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


def _highest_severity(severities: list[str]) -> str | None:
    if "critical" in severities:
        return "critical"
    if "warning" in severities:
        return "warning"
    if "info" in severities:
        return "info"
    return None


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


def _build_export_readiness_reason_codes(
    *,
    export_artifact_id: str | None,
    export_trace_key: str | None,
    quote_reference: str | None,
    snapshot_version: str | None,
    source_trace_key: str | None,
    snapshot_trace_key: str | None,
    source_event_bundle: dict[str, Any],
    warning_summary: dict[str, Any],
    warning_counts: dict[str, int],
) -> list[str]:
    ordered_reasons: list[tuple[str, bool]] = [
        ("missing_export_artifact", not _is_present(export_artifact_id)),
        ("missing_export_trace", not _is_present(export_trace_key)),
        ("missing_quote_reference", not _is_present(quote_reference)),
        ("missing_snapshot_version", not _is_present(snapshot_version)),
        ("missing_source_trace", not _is_present(source_trace_key)),
        ("missing_snapshot_trace", not _is_present(snapshot_trace_key)),
        ("missing_source_event", not bool(source_event_bundle.get("hasSourceEvent"))),
        ("missing_snapshot_event", not bool(source_event_bundle.get("hasSnapshotEvent"))),
        ("critical_warning_present", bool(warning_summary.get("hasCritical"))),
        (
            "warning_present",
            int(warning_counts.get("total", 0)) > 0 and not bool(warning_summary.get("hasCritical")),
        ),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_export_readiness(reason_codes: list[str]) -> str:
    blocked_codes = {
        "critical_warning_present",
        "missing_export_artifact",
        "missing_export_trace",
        "missing_quote_reference",
        "missing_snapshot_version",
    }
    conditional_codes = {
        "missing_source_trace",
        "missing_snapshot_trace",
        "missing_source_event",
        "missing_snapshot_event",
        "warning_present",
    }

    if any(code in blocked_codes for code in reason_codes):
        return "blocked"
    if any(code in conditional_codes for code in reason_codes):
        return "conditional"
    return "ready"


def _build_export_readiness_label(readiness: str) -> str:
    if readiness == "ready":
        return "Export Ready"
    if readiness == "conditional":
        return "Conditionally Export Ready"
    return "Export Blocked"


def _build_audit_completeness(
    *,
    source_trace_key: str | None,
    snapshot_trace_key: str | None,
    source_event_bundle: dict[str, Any],
    quote_reference: str | None,
    snapshot_version: str | None,
    captured_at: str | None,
) -> str:
    signals = [
        _is_present(source_trace_key),
        _is_present(snapshot_trace_key),
        bool(source_event_bundle.get("isComplete")),
        _is_present(quote_reference),
        _is_present(snapshot_version),
        _is_present(captured_at),
    ]
    if all(signals):
        return "complete"
    if any(signals):
        return "partial"
    return "minimal"


def _build_audit_completeness_label(completeness: str) -> str:
    if completeness == "complete":
        return "Audit Complete"
    if completeness == "partial":
        return "Audit Partial"
    return "Audit Minimal"


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


def _is_present(value: str | None) -> bool:
    return bool(value and value.strip())


def _integration_bridge_value(
    normalized_result: dict[str, Any],
    key: str,
) -> Any:
    if normalized_result.get("executionState") != "mock_executed":
        return None
    return normalized_result.get(key)


def _integration_payload_bridge_value(
    normalized_result: dict[str, Any],
    key: str,
) -> Any:
    if normalized_result.get("executionState") != "mock_executed":
        return None
    payload = normalized_result.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload.get(key)
