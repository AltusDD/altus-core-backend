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
    integration_result_type = _integration_bridge_value(
        corelogic_integration.normalized_result,
        "resultType",
    )
    integration_execution_state = _integration_bridge_value(
        corelogic_integration.normalized_result,
        "executionState",
    )
    integration_quote_reference = _integration_bridge_value(
        corelogic_integration.normalized_result,
        "quoteReference",
    )
    integration_snapshot_version = _integration_bridge_value(
        corelogic_integration.normalized_result,
        "snapshotVersion",
    )
    integration_payload_profile = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "profile",
    )
    integration_estimated_total_title_cost = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedTotalTitleCost",
    )
    integration_currency = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "currency",
    )
    integration_estimated_title_fee = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedTitleFee",
    )
    integration_estimated_settlement_fee = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedSettlementFee",
    )
    integration_estimated_recording_fee = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedRecordingFee",
    )
    integration_estimated_search_fee = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedSearchFee",
    )
    integration_estimated_misc_fee = _integration_payload_bridge_value(
        corelogic_integration.normalized_result,
        "estimatedMiscFee",
    )
    integration_fee_line_sum = _build_integration_fee_line_sum(
        integration_mode=corelogic_integration.mode,
        integration_result_type=integration_result_type,
        integration_execution_state=integration_execution_state,
        integration_estimated_title_fee=integration_estimated_title_fee,
        integration_estimated_settlement_fee=integration_estimated_settlement_fee,
        integration_estimated_recording_fee=integration_estimated_recording_fee,
        integration_estimated_search_fee=integration_estimated_search_fee,
        integration_estimated_misc_fee=integration_estimated_misc_fee,
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
    )
    integration_fee_delta = _build_integration_fee_delta(
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
        integration_fee_line_sum=integration_fee_line_sum,
    )
    integration_fee_reconciliation_status = _build_integration_fee_reconciliation_status(
        integration_fee_line_sum=integration_fee_line_sum,
        integration_fee_delta=integration_fee_delta,
    )
    integration_has_artifact = _build_integration_presence_flag(
        integration_execution_state=integration_execution_state,
        values=[corelogic_integration.artifact_type, corelogic_integration.artifact_id],
    )
    integration_has_trace = _build_integration_presence_flag(
        integration_execution_state=integration_execution_state,
        values=[corelogic_integration.trace_key],
    )
    integration_has_event = _build_integration_presence_flag(
        integration_execution_state=integration_execution_state,
        values=[corelogic_integration.event_type, corelogic_integration.event_ref],
    )
    integration_bundle_status = _build_integration_bundle_status(
        integration_mode=corelogic_integration.mode,
        integration_result_type=integration_result_type,
        integration_execution_state=integration_execution_state,
        integration_has_artifact=integration_has_artifact,
        integration_has_trace=integration_has_trace,
        integration_has_event=integration_has_event,
    )
    integration_export_reason_codes = _build_integration_export_reason_codes(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_artifact_type=corelogic_integration.artifact_type,
        integration_artifact_id=corelogic_integration.artifact_id,
        integration_trace_key=corelogic_integration.trace_key,
        integration_event_type=corelogic_integration.event_type,
        integration_event_ref=corelogic_integration.event_ref,
        integration_quote_reference=integration_quote_reference,
        integration_snapshot_version=integration_snapshot_version,
        integration_payload_profile=integration_payload_profile,
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
        integration_currency=integration_currency,
        integration_fee_line_sum=integration_fee_line_sum,
        integration_fee_delta=integration_fee_delta,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
        integration_fee_reconciliation_match=_build_integration_fee_reconciliation_match(
            integration_fee_reconciliation_status,
        ),
    )
    integration_export_readiness = _build_integration_export_readiness(
        integration_export_reason_codes=integration_export_reason_codes,
    )
    integration_audit_completeness = _build_integration_audit_completeness(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_result_type=integration_result_type,
        integration_bundle_status=integration_bundle_status,
        integration_quote_reference=integration_quote_reference,
        integration_snapshot_version=integration_snapshot_version,
        integration_payload_profile=integration_payload_profile,
        integration_currency=integration_currency,
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
        integration_fee_reconciliation_match=_build_integration_fee_reconciliation_match(
            integration_fee_reconciliation_status,
        ),
    )
    integration_fee_reconciliation_match = _build_integration_fee_reconciliation_match(
        integration_fee_reconciliation_status,
    )
    integration_summary_status = _build_integration_summary_status(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_export_readiness=integration_export_readiness,
        integration_guard_summary=corelogic_integration.guard_summary,
        integration_audit_completeness=integration_audit_completeness,
    )
    integration_summary_priority = _build_integration_summary_priority(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_live_ready=corelogic_integration.live_ready,
        integration_guard_summary=corelogic_integration.guard_summary,
        integration_export_readiness=integration_export_readiness,
        integration_audit_completeness=integration_audit_completeness,
    )
    integration_summary_reason_codes = _build_integration_summary_reason_codes(
        integration_summary_priority=integration_summary_priority,
    )
    integration_display_badge = _build_integration_display_badge(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_summary_priority=integration_summary_priority,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
    )
    integration_operator_action = _build_integration_operator_action(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_live_ready=corelogic_integration.live_ready,
        integration_export_readiness=integration_export_readiness,
        integration_audit_completeness=integration_audit_completeness,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
        integration_fee_reconciliation_match=integration_fee_reconciliation_match,
    )
    integration_operator_snapshot_status = _build_integration_operator_snapshot_status(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_operator_action=integration_operator_action,
        integration_operator_action_blocking=_build_integration_operator_action_blocking(
            integration_operator_action,
        ),
        integration_export_readiness=integration_export_readiness,
        integration_audit_completeness=integration_audit_completeness,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
    )
    integration_operator_card_status = _build_integration_operator_card_status(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_export_readiness=integration_export_readiness,
        integration_audit_completeness=integration_audit_completeness,
        integration_operator_action=integration_operator_action,
        integration_operator_action_blocking=_build_integration_operator_action_blocking(
            integration_operator_action,
        ),
        integration_operator_snapshot_status=integration_operator_snapshot_status,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
    )
    integration_export_packet_missing = _build_integration_export_packet_missing(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_quote_reference=integration_quote_reference,
        integration_snapshot_version=integration_snapshot_version,
        integration_currency=integration_currency,
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
        integration_fee_reconciliation_match=integration_fee_reconciliation_match,
    )
    integration_export_packet_status = _build_integration_export_packet_status(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_export_readiness=integration_export_readiness,
        integration_operator_card_status=integration_operator_card_status,
        integration_export_packet_missing=integration_export_packet_missing,
    )
    integration_export_packet_completeness = _build_integration_export_packet_completeness(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_bundle_status=integration_bundle_status,
        integration_quote_reference=integration_quote_reference,
        integration_snapshot_version=integration_snapshot_version,
        integration_currency=integration_currency,
        integration_estimated_total_title_cost=integration_estimated_total_title_cost,
        integration_fee_reconciliation_status=integration_fee_reconciliation_status,
        integration_fee_reconciliation_match=integration_fee_reconciliation_match,
    )
    integration_export_packet_ready = _build_integration_export_packet_ready(
        integration_export_packet_status=integration_export_packet_status,
        integration_export_packet_completeness=integration_export_packet_completeness,
        integration_export_packet_missing=integration_export_packet_missing,
    )
    integration_export_packet_summary_status = _build_integration_export_packet_summary_status(
        integration_mode=corelogic_integration.mode,
        integration_execution_state=integration_execution_state,
        integration_export_packet_status=integration_export_packet_status,
        integration_export_packet_completeness=integration_export_packet_completeness,
        integration_export_packet_missing=integration_export_packet_missing,
        integration_export_packet_ready=integration_export_packet_ready,
        integration_operator_card_status=integration_operator_card_status,
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
            "integrationResultType": integration_result_type,
            "integrationExecutionState": integration_execution_state,
            "integrationQuoteReference": integration_quote_reference,
            "integrationSnapshotVersion": integration_snapshot_version,
            "integrationPayloadProfile": integration_payload_profile,
            "integrationEstimatedTotalTitleCost": integration_estimated_total_title_cost,
            "integrationCurrency": integration_currency,
            "integrationEstimatedTitleFee": integration_estimated_title_fee,
            "integrationEstimatedSettlementFee": integration_estimated_settlement_fee,
            "integrationEstimatedRecordingFee": integration_estimated_recording_fee,
            "integrationEstimatedSearchFee": integration_estimated_search_fee,
            "integrationEstimatedMiscFee": integration_estimated_misc_fee,
            "integrationFeeLineSum": integration_fee_line_sum,
            "integrationFeeDelta": integration_fee_delta,
            "integrationFeeReconciliationStatus": integration_fee_reconciliation_status,
            "integrationFeeReconciliationLabel": _build_integration_fee_reconciliation_label(
                integration_fee_reconciliation_status,
            ),
            "integrationFeeReconciliationMatch": integration_fee_reconciliation_match,
            "integrationBundleStatus": integration_bundle_status,
            "integrationBundleStatusLabel": _build_integration_bundle_status_label(
                integration_bundle_status,
            ),
            "integrationHasArtifact": integration_has_artifact,
            "integrationHasTrace": integration_has_trace,
            "integrationHasEvent": integration_has_event,
            "integrationIsExportReady": _build_integration_is_export_ready(
                integration_bundle_status=integration_bundle_status,
                integration_quote_reference=integration_quote_reference,
                integration_snapshot_version=integration_snapshot_version,
                integration_currency=integration_currency,
                integration_estimated_total_title_cost=integration_estimated_total_title_cost,
            ),
            "integrationExportReadiness": integration_export_readiness,
            "integrationExportReadinessLabel": _build_integration_export_readiness_label(
                integration_export_readiness,
            ),
            "integrationExportReasonCodes": integration_export_reason_codes,
            "integrationAuditCompleteness": integration_audit_completeness,
            "integrationAuditCompletenessLabel": _build_integration_audit_completeness_label(
                integration_audit_completeness,
            ),
            "integrationSummaryStatus": integration_summary_status,
            "integrationSummaryStatusLabel": _build_integration_summary_status_label(
                integration_summary_status,
            ),
            "integrationSummaryPriority": integration_summary_priority,
            "integrationSummaryPriorityLabel": _build_integration_summary_priority_label(
                integration_summary_priority,
            ),
            "integrationSummaryReasonCodes": integration_summary_reason_codes,
            "integrationDisplayBadge": integration_display_badge,
            "integrationDisplayBadgeLabel": _build_integration_display_badge_label(
                integration_display_badge,
            ),
            "integrationDisplaySeverity": _build_integration_display_severity(
                integration_display_badge,
            ),
            "integrationDisplayOrder": _build_integration_display_order(
                integration_display_badge,
            ),
            "integrationDisplayReason": _build_integration_display_reason(
                integration_display_badge,
            ),
            "integrationOperatorAction": integration_operator_action,
            "integrationOperatorActionLabel": _build_integration_operator_action_label(
                integration_operator_action,
            ),
            "integrationOperatorActionPriority": _build_integration_operator_action_priority(
                integration_operator_action,
            ),
            "integrationOperatorActionReasonCodes": _build_integration_operator_action_reason_codes(
                integration_operator_action,
            ),
            "integrationOperatorActionBlocking": _build_integration_operator_action_blocking(
                integration_operator_action,
            ),
            "integrationOperatorSnapshotStatus": integration_operator_snapshot_status,
            "integrationOperatorSnapshotLabel": _build_integration_operator_snapshot_label(
                integration_operator_snapshot_status,
            ),
            "integrationOperatorSnapshotSeverity": _build_integration_operator_snapshot_severity(
                integration_operator_snapshot_status,
            ),
            "integrationOperatorSnapshotOrder": _build_integration_operator_snapshot_order(
                integration_operator_snapshot_status,
            ),
            "integrationOperatorSnapshotReasonCodes": _build_integration_operator_snapshot_reason_codes(
                integration_operator_snapshot_status,
            ),
            "integrationOperatorCardStatus": integration_operator_card_status,
            "integrationOperatorCardLabel": _build_integration_operator_card_label(
                integration_operator_card_status,
            ),
            "integrationOperatorCardSeverity": _build_integration_operator_card_severity(
                integration_operator_card_status,
            ),
            "integrationOperatorCardOrder": _build_integration_operator_card_order(
                integration_operator_card_status,
            ),
            "integrationOperatorCardReasonCodes": _build_integration_operator_card_reason_codes(
                integration_operator_card_status,
            ),
            "integrationExportPacketStatus": integration_export_packet_status,
            "integrationExportPacketLabel": _build_integration_export_packet_label(
                integration_export_packet_status,
            ),
            "integrationExportPacketCompleteness": integration_export_packet_completeness,
            "integrationExportPacketMissing": integration_export_packet_missing,
            "integrationExportPacketReady": integration_export_packet_ready,
            "integrationExportPacketSummaryStatus": integration_export_packet_summary_status,
            "integrationExportPacketSummaryLabel": _build_integration_export_packet_summary_label(
                integration_export_packet_summary_status,
            ),
            "integrationExportPacketSummaryPriority": _build_integration_export_packet_summary_priority(
                integration_export_packet_summary_status,
            ),
            "integrationExportPacketSummaryReasonCodes": _build_integration_export_packet_summary_reason_codes(
                integration_export_packet_summary_status,
            ),
            "integrationExportPacketSummaryBlocking": _build_integration_export_packet_summary_blocking(
                integration_export_packet_summary_status,
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


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


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


def _build_integration_fee_line_sum(
    *,
    integration_mode: str,
    integration_result_type: Any,
    integration_execution_state: Any,
    integration_estimated_title_fee: Any,
    integration_estimated_settlement_fee: Any,
    integration_estimated_recording_fee: Any,
    integration_estimated_search_fee: Any,
    integration_estimated_misc_fee: Any,
    integration_estimated_total_title_cost: Any,
) -> float | None:
    if integration_mode != "mock":
        return None
    if integration_result_type != "mock_title_quote":
        return None
    if integration_execution_state != "mock_executed":
        return None
    fee_values = [
        integration_estimated_title_fee,
        integration_estimated_settlement_fee,
        integration_estimated_recording_fee,
        integration_estimated_search_fee,
        integration_estimated_misc_fee,
        integration_estimated_total_title_cost,
    ]
    if any(not isinstance(value, (int, float)) for value in fee_values):
        return None
    return float(
        integration_estimated_title_fee
        + integration_estimated_settlement_fee
        + integration_estimated_recording_fee
        + integration_estimated_search_fee
        + integration_estimated_misc_fee
    )


def _build_integration_fee_delta(
    *,
    integration_estimated_total_title_cost: Any,
    integration_fee_line_sum: float | None,
) -> float | None:
    if integration_fee_line_sum is None:
        return None
    if not isinstance(integration_estimated_total_title_cost, (int, float)):
        return None
    return float(integration_estimated_total_title_cost - integration_fee_line_sum)


def _build_integration_fee_reconciliation_status(
    *,
    integration_fee_line_sum: float | None,
    integration_fee_delta: float | None,
) -> str | None:
    if integration_fee_line_sum is None or integration_fee_delta is None:
        return None
    if integration_fee_delta == 0.0:
        return "matched"
    return "mismatched"


def _build_integration_fee_reconciliation_label(
    integration_fee_reconciliation_status: str | None,
) -> str | None:
    if integration_fee_reconciliation_status == "matched":
        return "Fee Reconciliation Matched"
    if integration_fee_reconciliation_status == "mismatched":
        return "Fee Reconciliation Mismatched"
    return None


def _build_integration_fee_reconciliation_match(
    integration_fee_reconciliation_status: str | None,
) -> bool | None:
    if integration_fee_reconciliation_status == "matched":
        return True
    if integration_fee_reconciliation_status == "mismatched":
        return False
    return None


def _build_integration_presence_flag(
    *,
    integration_execution_state: Any,
    values: list[Any],
) -> bool | None:
    if integration_execution_state != "mock_executed":
        return None
    return all(_is_non_empty_string(value) for value in values)


def _build_integration_bundle_status(
    *,
    integration_mode: str,
    integration_result_type: Any,
    integration_execution_state: Any,
    integration_has_artifact: bool | None,
    integration_has_trace: bool | None,
    integration_has_event: bool | None,
) -> str | None:
    if integration_mode != "mock":
        return None
    if integration_result_type != "mock_title_quote":
        return None
    if integration_execution_state != "mock_executed":
        return None
    if integration_has_artifact and integration_has_trace and integration_has_event:
        return "complete"
    if any(value is True for value in [integration_has_artifact, integration_has_trace, integration_has_event]):
        return "partial"
    return "missing"


def _build_integration_bundle_status_label(
    integration_bundle_status: str | None,
) -> str | None:
    if integration_bundle_status == "complete":
        return "Integration Bundle Complete"
    if integration_bundle_status == "partial":
        return "Integration Bundle Partial"
    if integration_bundle_status == "missing":
        return "Integration Bundle Missing"
    return None


def _build_integration_is_export_ready(
    *,
    integration_bundle_status: str | None,
    integration_quote_reference: Any,
    integration_snapshot_version: Any,
    integration_currency: Any,
    integration_estimated_total_title_cost: Any,
) -> bool | None:
    if integration_bundle_status is None:
        return None
    return bool(
        integration_bundle_status == "complete"
        and _is_non_empty_string(integration_quote_reference)
        and _is_non_empty_string(integration_snapshot_version)
        and _is_non_empty_string(integration_currency)
        and integration_estimated_total_title_cost is not None
    )


def _build_integration_export_reason_codes(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_artifact_type: Any,
    integration_artifact_id: Any,
    integration_trace_key: Any,
    integration_event_type: Any,
    integration_event_ref: Any,
    integration_quote_reference: Any,
    integration_snapshot_version: Any,
    integration_payload_profile: Any,
    integration_estimated_total_title_cost: Any,
    integration_currency: Any,
    integration_fee_line_sum: Any,
    integration_fee_delta: Any,
    integration_fee_reconciliation_status: Any,
    integration_fee_reconciliation_match: Any,
) -> list[str] | None:
    if integration_mode != "mock" or integration_execution_state != "mock_executed":
        return None

    ordered_reasons: list[tuple[str, bool]] = [
        (
            "missing_integration_artifact",
            not (_is_non_empty_string(integration_artifact_type) and _is_non_empty_string(integration_artifact_id)),
        ),
        ("missing_integration_trace", not _is_non_empty_string(integration_trace_key)),
        (
            "missing_integration_event",
            not (_is_non_empty_string(integration_event_type) and _is_non_empty_string(integration_event_ref)),
        ),
        ("missing_integration_quote_reference", not _is_non_empty_string(integration_quote_reference)),
        ("missing_integration_snapshot_version", not _is_non_empty_string(integration_snapshot_version)),
        ("missing_integration_currency", not _is_non_empty_string(integration_currency)),
        ("missing_integration_total_cost", integration_estimated_total_title_cost is None),
        ("missing_integration_payload_profile", not _is_non_empty_string(integration_payload_profile)),
        (
            "fee_reconciliation_missing",
            any(
                value is None
                for value in [
                    integration_fee_line_sum,
                    integration_fee_delta,
                    integration_fee_reconciliation_status,
                    integration_fee_reconciliation_match,
                ]
            ),
        ),
        (
            "fee_reconciliation_mismatch",
            integration_fee_reconciliation_status == "mismatched" or integration_fee_reconciliation_match is False,
        ),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_export_readiness(
    *,
    integration_export_reason_codes: list[str] | None,
) -> str | None:
    if integration_export_reason_codes is None:
        return None

    blocked_codes = {
        "missing_integration_artifact",
        "missing_integration_trace",
        "missing_integration_event",
        "missing_integration_quote_reference",
        "missing_integration_snapshot_version",
        "missing_integration_currency",
        "missing_integration_total_cost",
    }
    conditional_codes = {
        "missing_integration_payload_profile",
        "fee_reconciliation_missing",
        "fee_reconciliation_mismatch",
    }

    if any(code in blocked_codes for code in integration_export_reason_codes):
        return "blocked"
    if any(code in conditional_codes for code in integration_export_reason_codes):
        return "conditional"
    return "ready"


def _build_integration_export_readiness_label(
    integration_export_readiness: str | None,
) -> str | None:
    if integration_export_readiness == "ready":
        return "Integration Export Ready"
    if integration_export_readiness == "conditional":
        return "Integration Export Conditional"
    if integration_export_readiness == "blocked":
        return "Integration Export Blocked"
    return None


def _build_integration_audit_completeness(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_result_type: Any,
    integration_bundle_status: Any,
    integration_quote_reference: Any,
    integration_snapshot_version: Any,
    integration_payload_profile: Any,
    integration_currency: Any,
    integration_estimated_total_title_cost: Any,
    integration_fee_reconciliation_match: Any,
) -> str | None:
    if integration_mode != "mock" or integration_execution_state != "mock_executed":
        return None

    signals = [
        integration_bundle_status == "complete",
        _is_non_empty_string(integration_quote_reference),
        _is_non_empty_string(integration_snapshot_version),
        _is_non_empty_string(integration_payload_profile),
        _is_non_empty_string(integration_currency),
        integration_estimated_total_title_cost is not None,
        integration_fee_reconciliation_match is True,
    ]
    if all(signals):
        return "complete"
    if any(signals):
        return "partial"
    return "minimal"


def _build_integration_audit_completeness_label(
    integration_audit_completeness: str | None,
) -> str | None:
    if integration_audit_completeness == "complete":
        return "Integration Audit Complete"
    if integration_audit_completeness == "partial":
        return "Integration Audit Partial"
    if integration_audit_completeness == "minimal":
        return "Integration Audit Minimal"
    return None


def _build_integration_summary_status(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_export_readiness: str | None,
    integration_guard_summary: str | None,
    integration_audit_completeness: str | None,
) -> str | None:
    if integration_mode != "mock" or integration_execution_state != "mock_executed":
        return None
    if integration_export_readiness == "blocked" or integration_guard_summary in {
        "blocked_live_calls_not_allowed",
        "blocked_missing_credentials",
    }:
        return "blocked"
    if integration_export_readiness == "conditional" or integration_audit_completeness in {
        "partial",
        "minimal",
    }:
        return "conditional"
    if integration_export_readiness == "ready" and integration_audit_completeness == "complete":
        return "ready"
    return None


def _build_integration_summary_status_label(
    integration_summary_status: str | None,
) -> str | None:
    if integration_summary_status == "ready":
        return "Integration Summary Ready"
    if integration_summary_status == "conditional":
        return "Integration Summary Conditional"
    if integration_summary_status == "blocked":
        return "Integration Summary Blocked"
    return None


def _build_integration_summary_priority(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_live_ready: bool,
    integration_guard_summary: str | None,
    integration_export_readiness: str | None,
    integration_audit_completeness: str | None,
) -> str | None:
    if integration_mode != "mock" or integration_execution_state != "mock_executed":
        return None
    if integration_export_readiness == "blocked":
        return "export_blocked"
    if integration_export_readiness == "conditional":
        return "export_conditional"
    if integration_export_readiness == "ready" and integration_audit_completeness == "partial":
        return "audit_partial"
    if integration_export_readiness == "ready" and integration_audit_completeness == "minimal":
        return "audit_minimal"
    if not integration_live_ready and integration_guard_summary in {
        "blocked_live_calls_not_allowed",
        "blocked_missing_credentials",
    }:
        return "live_blocked"
    if (
        integration_mode == "mock"
        and integration_export_readiness == "ready"
        and integration_audit_completeness == "complete"
    ):
        return "mock_ready"
    return None


def _build_integration_summary_priority_label(
    integration_summary_priority: str | None,
) -> str | None:
    if integration_summary_priority == "export_blocked":
        return "Export Blocked"
    if integration_summary_priority == "export_conditional":
        return "Export Conditional"
    if integration_summary_priority == "audit_partial":
        return "Audit Partial"
    if integration_summary_priority == "audit_minimal":
        return "Audit Minimal"
    if integration_summary_priority == "live_blocked":
        return "Live Blocked"
    if integration_summary_priority == "mock_ready":
        return "Mock Ready"
    if integration_summary_priority == "ready":
        return "Ready"
    return None


def _build_integration_summary_reason_codes(
    *,
    integration_summary_priority: str | None,
) -> list[str] | None:
    if integration_summary_priority is None:
        return None
    ordered_reasons = [
        ("summary_export_blocked", integration_summary_priority == "export_blocked"),
        ("summary_export_conditional", integration_summary_priority == "export_conditional"),
        ("summary_audit_partial", integration_summary_priority == "audit_partial"),
        ("summary_audit_minimal", integration_summary_priority == "audit_minimal"),
        ("summary_live_blocked", integration_summary_priority == "live_blocked"),
        ("summary_mock_ready", integration_summary_priority == "mock_ready"),
        ("summary_ready", integration_summary_priority == "ready"),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_display_badge(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_summary_priority: str | None,
    integration_fee_reconciliation_status: str | None,
) -> str | None:
    if integration_mode != "mock" or integration_execution_state != "mock_executed":
        return None
    if integration_summary_priority == "export_blocked":
        return "blocked"
    if (
        integration_summary_priority == "export_conditional"
        or integration_fee_reconciliation_status == "mismatched"
    ):
        return "conditional"
    if integration_summary_priority == "audit_partial":
        return "audit_partial"
    if integration_summary_priority == "audit_minimal":
        return "audit_minimal"
    if integration_summary_priority == "mock_ready":
        return "mock_ready"
    if integration_summary_priority == "ready":
        return "ready"
    return None


def _build_integration_display_badge_label(
    integration_display_badge: str | None,
) -> str | None:
    if integration_display_badge == "blocked":
        return "Integration Blocked"
    if integration_display_badge == "conditional":
        return "Integration Conditional"
    if integration_display_badge == "audit_partial":
        return "Integration Audit Partial"
    if integration_display_badge == "audit_minimal":
        return "Integration Audit Minimal"
    if integration_display_badge == "mock_ready":
        return "Integration Mock Ready"
    if integration_display_badge == "ready":
        return "Integration Ready"
    return None


def _build_integration_display_severity(
    integration_display_badge: str | None,
) -> str | None:
    if integration_display_badge == "blocked":
        return "critical"
    if integration_display_badge in {"conditional", "audit_partial", "audit_minimal"}:
        return "warning"
    if integration_display_badge in {"mock_ready", "ready"}:
        return "info"
    return None


def _build_integration_display_order(
    integration_display_badge: str | None,
) -> int | None:
    mapping = {
        "blocked": 1,
        "conditional": 2,
        "audit_partial": 3,
        "audit_minimal": 4,
        "mock_ready": 5,
        "ready": 6,
    }
    return mapping.get(integration_display_badge)


def _build_integration_display_reason(
    integration_display_badge: str | None,
) -> str | None:
    mapping = {
        "blocked": "export_blocked",
        "conditional": "export_conditional",
        "audit_partial": "audit_partial",
        "audit_minimal": "audit_minimal",
        "mock_ready": "mock_ready",
        "ready": "live_ready",
    }
    return mapping.get(integration_display_badge)


def _build_integration_operator_action(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_live_ready: bool,
    integration_export_readiness: str | None,
    integration_audit_completeness: str | None,
    integration_fee_reconciliation_status: str | None,
    integration_fee_reconciliation_match: bool | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    if integration_export_readiness == "blocked":
        return "resolve_export_blockers"
    if (
        integration_fee_reconciliation_status == "mismatched"
        or integration_fee_reconciliation_match is False
    ):
        return "review_fee_mismatch"
    if integration_export_readiness == "conditional":
        return "resolve_export_warnings"
    if integration_audit_completeness in {"partial", "minimal"}:
        return "complete_audit_data"
    if (
        integration_mode == "mock"
        and integration_export_readiness == "ready"
        and integration_audit_completeness == "complete"
    ):
        return "monitor_mock_state"
    if (
        integration_mode == "live"
        and integration_live_ready
        and integration_export_readiness == "ready"
        and integration_audit_completeness == "complete"
    ):
        return "ready_no_action"
    return None


def _build_integration_operator_action_label(
    integration_operator_action: str | None,
) -> str | None:
    mapping = {
        "resolve_export_blockers": "Resolve Export Blockers",
        "resolve_export_warnings": "Resolve Export Warnings",
        "complete_audit_data": "Complete Audit Data",
        "review_fee_mismatch": "Review Fee Mismatch",
        "monitor_mock_state": "Monitor Mock State",
        "ready_no_action": "Ready No Action",
    }
    return mapping.get(integration_operator_action)


def _build_integration_operator_action_priority(
    integration_operator_action: str | None,
) -> int | None:
    mapping = {
        "resolve_export_blockers": 1,
        "review_fee_mismatch": 2,
        "resolve_export_warnings": 3,
        "complete_audit_data": 4,
        "monitor_mock_state": 5,
        "ready_no_action": 6,
    }
    return mapping.get(integration_operator_action)


def _build_integration_operator_action_reason_codes(
    integration_operator_action: str | None,
) -> list[str] | None:
    if integration_operator_action is None:
        return None
    ordered_reasons = [
        ("operator_export_blocked", integration_operator_action == "resolve_export_blockers"),
        ("operator_fee_mismatch", integration_operator_action == "review_fee_mismatch"),
        ("operator_export_conditional", integration_operator_action == "resolve_export_warnings"),
        ("operator_audit_incomplete", integration_operator_action == "complete_audit_data"),
        ("operator_mock_monitor", integration_operator_action == "monitor_mock_state"),
        ("operator_ready", integration_operator_action == "ready_no_action"),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_operator_action_blocking(
    integration_operator_action: str | None,
) -> bool | None:
    if integration_operator_action is None:
        return None
    return integration_operator_action in {
        "resolve_export_blockers",
        "review_fee_mismatch",
    }


def _build_integration_operator_snapshot_status(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_operator_action: str | None,
    integration_operator_action_blocking: bool | None,
    integration_export_readiness: str | None,
    integration_audit_completeness: str | None,
    integration_fee_reconciliation_status: str | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    if (
        integration_operator_action_blocking is True
        and integration_operator_action == "resolve_export_blockers"
    ) or integration_export_readiness == "blocked":
        return "blocked"
    if (
        integration_operator_action == "resolve_export_warnings"
        or integration_export_readiness == "conditional"
    ):
        return "conditional"
    if (
        integration_operator_action in {"review_fee_mismatch", "complete_audit_data"}
        or integration_fee_reconciliation_status == "mismatched"
        or integration_audit_completeness in {"partial", "minimal"}
    ):
        return "review"
    if integration_operator_action == "monitor_mock_state":
        return "monitor"
    if integration_operator_action == "ready_no_action":
        return "ready"
    return None


def _build_integration_operator_snapshot_label(
    integration_operator_snapshot_status: str | None,
) -> str | None:
    mapping = {
        "blocked": "Operator Snapshot Blocked",
        "conditional": "Operator Snapshot Conditional",
        "review": "Operator Snapshot Review",
        "monitor": "Operator Snapshot Monitor",
        "ready": "Operator Snapshot Ready",
    }
    return mapping.get(integration_operator_snapshot_status)


def _build_integration_operator_snapshot_severity(
    integration_operator_snapshot_status: str | None,
) -> str | None:
    if integration_operator_snapshot_status == "blocked":
        return "critical"
    if integration_operator_snapshot_status in {"conditional", "review"}:
        return "warning"
    if integration_operator_snapshot_status in {"monitor", "ready"}:
        return "info"
    return None


def _build_integration_operator_snapshot_order(
    integration_operator_snapshot_status: str | None,
) -> int | None:
    mapping = {
        "blocked": 1,
        "conditional": 2,
        "review": 3,
        "monitor": 4,
        "ready": 5,
    }
    return mapping.get(integration_operator_snapshot_status)


def _build_integration_operator_snapshot_reason_codes(
    integration_operator_snapshot_status: str | None,
) -> list[str] | None:
    if integration_operator_snapshot_status is None:
        return None
    ordered_reasons = [
        ("snapshot_export_blocked", integration_operator_snapshot_status == "blocked"),
        ("snapshot_export_conditional", integration_operator_snapshot_status == "conditional"),
        ("snapshot_review_required", integration_operator_snapshot_status == "review"),
        ("snapshot_monitor_only", integration_operator_snapshot_status == "monitor"),
        ("snapshot_ready", integration_operator_snapshot_status == "ready"),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_operator_card_status(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_export_readiness: str | None,
    integration_audit_completeness: str | None,
    integration_operator_action: str | None,
    integration_operator_action_blocking: bool | None,
    integration_operator_snapshot_status: str | None,
    integration_fee_reconciliation_status: str | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    if (
        (
            integration_operator_action_blocking is True
            and integration_operator_action == "resolve_export_blockers"
        )
        or integration_export_readiness == "blocked"
        or integration_operator_snapshot_status == "blocked"
    ):
        return "blocked"
    if (
        integration_export_readiness == "conditional"
        or integration_operator_snapshot_status == "conditional"
    ):
        return "conditional"
    if (
        integration_operator_snapshot_status == "review"
        or integration_fee_reconciliation_status == "mismatched"
        or integration_audit_completeness in {"partial", "minimal"}
    ):
        return "review"
    if integration_operator_snapshot_status == "monitor":
        return "monitor"
    if integration_operator_snapshot_status == "ready":
        return "ready"
    return None


def _build_integration_operator_card_label(
    integration_operator_card_status: str | None,
) -> str | None:
    mapping = {
        "blocked": "Operator Card Blocked",
        "conditional": "Operator Card Conditional",
        "review": "Operator Card Review",
        "monitor": "Operator Card Monitor",
        "ready": "Operator Card Ready",
    }
    return mapping.get(integration_operator_card_status)


def _build_integration_operator_card_severity(
    integration_operator_card_status: str | None,
) -> str | None:
    if integration_operator_card_status == "blocked":
        return "critical"
    if integration_operator_card_status in {"conditional", "review"}:
        return "warning"
    if integration_operator_card_status in {"monitor", "ready"}:
        return "info"
    return None


def _build_integration_operator_card_order(
    integration_operator_card_status: str | None,
) -> int | None:
    mapping = {
        "blocked": 1,
        "conditional": 2,
        "review": 3,
        "monitor": 4,
        "ready": 5,
    }
    return mapping.get(integration_operator_card_status)


def _build_integration_operator_card_reason_codes(
    integration_operator_card_status: str | None,
) -> list[str] | None:
    if integration_operator_card_status is None:
        return None
    ordered_reasons = [
        ("card_export_blocked", integration_operator_card_status == "blocked"),
        ("card_export_conditional", integration_operator_card_status == "conditional"),
        ("card_review_required", integration_operator_card_status == "review"),
        ("card_monitor_only", integration_operator_card_status == "monitor"),
        ("card_ready", integration_operator_card_status == "ready"),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_export_packet_missing(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_quote_reference: Any,
    integration_snapshot_version: Any,
    integration_currency: Any,
    integration_estimated_total_title_cost: Any,
    integration_fee_reconciliation_status: str | None,
    integration_fee_reconciliation_match: bool | None,
) -> list[str] | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    ordered_missing = [
        ("quote_reference", not _is_non_empty_string(integration_quote_reference)),
        ("snapshot_version", not _is_non_empty_string(integration_snapshot_version)),
        ("currency", not _is_non_empty_string(integration_currency)),
        ("estimated_total_title_cost", integration_estimated_total_title_cost is None),
        (
            "fee_reconciliation",
            (
                integration_fee_reconciliation_status is None
                or integration_fee_reconciliation_match is None
                or integration_fee_reconciliation_status == "mismatched"
                or integration_fee_reconciliation_match is False
            ),
        ),
    ]
    return [token for token, include in ordered_missing if include]


def _build_integration_export_packet_status(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_export_readiness: str | None,
    integration_operator_card_status: str | None,
    integration_export_packet_missing: list[str] | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    if (
        integration_export_readiness == "blocked"
        or integration_operator_card_status == "blocked"
    ):
        return "blocked"
    if (
        integration_export_readiness == "conditional"
        or integration_operator_card_status == "conditional"
        or bool(integration_export_packet_missing)
    ):
        return "conditional"
    return "ready"


def _build_integration_export_packet_label(
    integration_export_packet_status: str | None,
) -> str | None:
    mapping = {
        "ready": "Integration Export Packet Ready",
        "conditional": "Integration Export Packet Conditional",
        "blocked": "Integration Export Packet Blocked",
    }
    return mapping.get(integration_export_packet_status)


def _build_integration_export_packet_completeness(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_bundle_status: str | None,
    integration_quote_reference: Any,
    integration_snapshot_version: Any,
    integration_currency: Any,
    integration_estimated_total_title_cost: Any,
    integration_fee_reconciliation_status: str | None,
    integration_fee_reconciliation_match: bool | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    signals = [
        integration_bundle_status == "complete",
        _is_non_empty_string(integration_quote_reference),
        _is_non_empty_string(integration_snapshot_version),
        _is_non_empty_string(integration_currency),
        integration_estimated_total_title_cost is not None,
        integration_fee_reconciliation_status == "matched",
        integration_fee_reconciliation_match is True,
    ]
    if all(signals):
        return "complete"
    if any(signals):
        return "partial"
    return "minimal"


def _build_integration_export_packet_ready(
    *,
    integration_export_packet_status: str | None,
    integration_export_packet_completeness: str | None,
    integration_export_packet_missing: list[str] | None,
) -> bool | None:
    if (
        integration_export_packet_status is None
        or integration_export_packet_completeness is None
        or integration_export_packet_missing is None
    ):
        return None
    return (
        integration_export_packet_status == "ready"
        and integration_export_packet_completeness == "complete"
        and integration_export_packet_missing == []
    )


def _build_integration_export_packet_summary_status(
    *,
    integration_mode: str,
    integration_execution_state: Any,
    integration_export_packet_status: str | None,
    integration_export_packet_completeness: str | None,
    integration_export_packet_missing: list[str] | None,
    integration_export_packet_ready: bool | None,
    integration_operator_card_status: str | None,
) -> str | None:
    if integration_execution_state is None:
        return None
    if integration_mode == "mock" and integration_execution_state != "mock_executed":
        return None
    if integration_mode not in {"mock", "live"}:
        return None
    if (
        integration_export_packet_status == "blocked"
        or integration_operator_card_status == "blocked"
    ):
        return "blocked"
    if (
        integration_export_packet_status == "conditional"
        or integration_operator_card_status == "conditional"
        or integration_export_packet_completeness in {"partial", "minimal"}
        or bool(integration_export_packet_missing)
    ):
        return "conditional"
    if (
        integration_export_packet_status == "ready"
        and integration_export_packet_completeness == "complete"
        and integration_export_packet_ready is True
    ):
        return "ready"
    return None


def _build_integration_export_packet_summary_label(
    integration_export_packet_summary_status: str | None,
) -> str | None:
    mapping = {
        "ready": "Export Packet Summary Ready",
        "conditional": "Export Packet Summary Conditional",
        "blocked": "Export Packet Summary Blocked",
    }
    return mapping.get(integration_export_packet_summary_status)


def _build_integration_export_packet_summary_priority(
    integration_export_packet_summary_status: str | None,
) -> int | None:
    mapping = {
        "blocked": 1,
        "conditional": 2,
        "ready": 3,
    }
    return mapping.get(integration_export_packet_summary_status)


def _build_integration_export_packet_summary_reason_codes(
    integration_export_packet_summary_status: str | None,
) -> list[str] | None:
    if integration_export_packet_summary_status is None:
        return None
    ordered_reasons = [
        ("packet_summary_blocked", integration_export_packet_summary_status == "blocked"),
        ("packet_summary_conditional", integration_export_packet_summary_status == "conditional"),
        ("packet_summary_ready", integration_export_packet_summary_status == "ready"),
    ]
    return [code for code, include in ordered_reasons if include]


def _build_integration_export_packet_summary_blocking(
    integration_export_packet_summary_status: str | None,
) -> bool | None:
    if integration_export_packet_summary_status is None:
        return None
    return integration_export_packet_summary_status == "blocked"
