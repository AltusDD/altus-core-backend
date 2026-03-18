from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable


CORELOGIC_PROVIDER_KEY = "corelogic"
CORELOGIC_MODE_DISABLED = "disabled"
CORELOGIC_MODE_MOCK = "mock"
CORELOGIC_MODE_LIVE = "live"

CORELOGIC_STATE_INACTIVE = "inactive"
CORELOGIC_STATE_MOCK_READY = "mock_ready"
CORELOGIC_STATE_LIVE_BLOCKED = "live_blocked"
CORELOGIC_STATE_LIVE_READY = "live_ready"

_REASON_CODE_ORDER = (
    "integration_disabled",
    "mode_disabled",
    "mode_mock",
    "live_calls_not_allowed",
    "live_credentials_missing",
    "live_mode_enabled",
)


@dataclass(frozen=True)
class CoreLogicIntegrationScaffold:
    provider: str
    mode: str
    state: str
    state_label: str
    reason_codes: list[str]
    live_ready: bool
    live_ready_label: str
    credential_state: str
    credential_state_label: str
    guard_summary: str
    artifact_type: str | None
    artifact_id: str | None
    trace_key: str | None
    event_type: str | None
    event_ref: str | None
    mock_profile: str | None
    mock_profile_label: str | None
    mock_payload: dict[str, Any] | None
    normalized_result: dict[str, Any]


def resolve_corelogic_integration_scaffold(
    provider_context: dict[str, Any] | None,
    *,
    live_executor: Callable[[], Any] | None = None,
) -> CoreLogicIntegrationScaffold:
    del live_executor

    scaffold_context = _scaffold_context(provider_context)
    enabled = _resolve_enabled(scaffold_context)
    mode = _resolve_mode(scaffold_context)
    allow_live_calls = _resolve_allow_live_calls(scaffold_context)
    credential_state = _resolve_credential_state(scaffold_context)

    if not enabled:
        return _build_scaffold(
            mode=CORELOGIC_MODE_DISABLED if mode == CORELOGIC_MODE_DISABLED else mode,
            state=CORELOGIC_STATE_INACTIVE,
            reason_codes=["integration_disabled", "mode_disabled"] if mode == CORELOGIC_MODE_DISABLED else ["integration_disabled"],
            credential_state=credential_state,
            guard_summary="disabled",
            mock_payload=None,
        )

    if mode == CORELOGIC_MODE_DISABLED:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_INACTIVE,
            reason_codes=["mode_disabled"],
            credential_state=credential_state,
            guard_summary="disabled",
            mock_payload=None,
        )

    if mode == CORELOGIC_MODE_MOCK:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_MOCK_READY,
            reason_codes=["mode_mock"],
            credential_state=credential_state,
            guard_summary="mock",
            mock_payload=_build_mock_payload(),
        )

    if not allow_live_calls:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_LIVE_BLOCKED,
            reason_codes=["live_calls_not_allowed", "live_mode_enabled"],
            credential_state=credential_state,
            guard_summary="blocked_live_calls_not_allowed",
            mock_payload=None,
        )

    if credential_state != "present":
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_LIVE_BLOCKED,
            reason_codes=["live_credentials_missing", "live_mode_enabled"],
            credential_state=credential_state,
            guard_summary="blocked_missing_credentials",
            mock_payload=None,
        )

    return _build_scaffold(
        mode=mode,
        state=CORELOGIC_STATE_LIVE_READY,
        reason_codes=["live_mode_enabled"],
        credential_state=credential_state,
        guard_summary="ready_for_live",
        mock_payload=None,
    )


def _build_scaffold(
    *,
    mode: str,
    state: str,
    reason_codes: list[str],
    credential_state: str,
    guard_summary: str,
    mock_payload: dict[str, Any] | None,
) -> CoreLogicIntegrationScaffold:
    live_ready = guard_summary == "ready_for_live"
    return CoreLogicIntegrationScaffold(
        provider=CORELOGIC_PROVIDER_KEY,
        mode=mode,
        state=state,
        state_label=_build_state_label(state),
        reason_codes=_ordered_unique_reason_codes(reason_codes),
        live_ready=live_ready,
        live_ready_label=_build_live_ready_label(live_ready),
        credential_state=credential_state,
        credential_state_label=_build_credential_state_label(credential_state),
        guard_summary=guard_summary,
        artifact_type=_build_artifact_type(mode),
        artifact_id=_build_artifact_id(mode),
        trace_key=_build_trace_key(mode),
        event_type=_build_event_type(mode),
        event_ref=_build_event_ref(mode),
        mock_profile=_build_mock_profile(mode),
        mock_profile_label=_build_mock_profile_label(mode),
        mock_payload=mock_payload,
        normalized_result=_build_normalized_result(
            provider=CORELOGIC_PROVIDER_KEY,
            mode=mode,
            guard_summary=guard_summary,
            artifact_type=_build_artifact_type(mode),
            artifact_id=_build_artifact_id(mode),
            trace_key=_build_trace_key(mode),
            event_type=_build_event_type(mode),
            event_ref=_build_event_ref(mode),
            mock_payload=mock_payload,
        ),
    )


def _build_state_label(state: str) -> str:
    if state == CORELOGIC_STATE_MOCK_READY:
        return "Mock Integration Ready"
    if state == CORELOGIC_STATE_LIVE_BLOCKED:
        return "Live Integration Blocked"
    if state == CORELOGIC_STATE_LIVE_READY:
        return "Live Integration Ready"
    return "Integration Inactive"


def _build_live_ready_label(live_ready: bool) -> str:
    if live_ready:
        return "Live Integration Ready"
    return "Live Integration Not Ready"


def _build_credential_state_label(credential_state: str) -> str:
    if credential_state == "present":
        return "Credentials Present"
    if credential_state == "partial":
        return "Credentials Partial"
    return "Credentials Missing"


def _ordered_unique_reason_codes(reason_codes: list[str]) -> list[str]:
    reason_code_set = set(reason_codes)
    return [code for code in _REASON_CODE_ORDER if code in reason_code_set]


def _build_mock_payload() -> dict[str, Any]:
    return {
        "estimatedTitleFee": 1850.0,
        "estimatedSettlementFee": 950.0,
        "estimatedRecordingFee": 150.0,
        "estimatedSearchFee": 450.0,
        "estimatedMiscFee": 300.0,
        "estimatedTotalTitleCost": 3700.0,
        "currency": "USD",
        "profile": "title_quote_baseline",
    }


def _build_normalized_result(
    *,
    provider: str,
    mode: str,
    guard_summary: str,
    artifact_type: str | None,
    artifact_id: str | None,
    trace_key: str | None,
    event_type: str | None,
    event_ref: str | None,
    mock_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    if mode == CORELOGIC_MODE_MOCK:
        return {
            "provider": provider,
            "mode": mode,
            "executionState": "mock_executed",
            "resultType": "mock_title_quote",
            "artifactType": artifact_type,
            "artifactId": artifact_id,
            "traceKey": trace_key,
            "eventType": event_type,
            "eventRef": event_ref,
            "quoteReference": "CORELOGIC-MOCK-QUOTE-001",
            "snapshotVersion": "mock-v1",
            "warnings": [],
            "warningCodes": [],
            "warningSeverities": [],
            "warningFamilies": [],
            "payload": mock_payload,
        }

    if guard_summary in {"blocked_live_calls_not_allowed", "blocked_missing_credentials"} and mode == CORELOGIC_MODE_LIVE:
        return {
            "provider": provider,
            "mode": mode,
            "executionState": "live_blocked",
            "resultType": "blocked",
            "artifactType": None,
            "artifactId": None,
            "traceKey": None,
            "eventType": None,
            "eventRef": None,
            "quoteReference": None,
            "snapshotVersion": None,
            "warnings": [],
            "warningCodes": [],
            "warningSeverities": [],
            "warningFamilies": [],
            "payload": None,
        }

    return {
        "provider": provider,
        "mode": mode,
        "executionState": "not_executed",
        "resultType": "none",
        "artifactType": None,
        "artifactId": None,
        "traceKey": None,
        "eventType": None,
        "eventRef": None,
        "quoteReference": None,
        "snapshotVersion": None,
        "warnings": [],
        "warningCodes": [],
        "warningSeverities": [],
        "warningFamilies": [],
        "payload": None,
    }


def _build_artifact_type(mode: str) -> str | None:
    if mode == CORELOGIC_MODE_MOCK:
        return "corelogic_mock_payload"
    return None


def _build_artifact_id(mode: str) -> str | None:
    if mode == CORELOGIC_MODE_MOCK:
        return "corelogic-mock-title-quote-v1"
    return None


def _build_trace_key(mode: str) -> str | None:
    artifact_id = _build_artifact_id(mode)
    if mode == CORELOGIC_MODE_MOCK and artifact_id:
        return f"{CORELOGIC_PROVIDER_KEY}:mock:{artifact_id}"
    return None


def _build_event_type(mode: str) -> str | None:
    if mode == CORELOGIC_MODE_MOCK:
        return "corelogic_mock_title_quote"
    return None


def _build_event_ref(mode: str) -> str | None:
    trace_key = _build_trace_key(mode)
    if trace_key is None:
        return None
    return f"integration-event:{trace_key}"


def _build_mock_profile(mode: str) -> str | None:
    if mode == CORELOGIC_MODE_MOCK:
        return "title_quote_baseline"
    return None


def _build_mock_profile_label(mode: str) -> str | None:
    if mode == CORELOGIC_MODE_MOCK:
        return "Title Quote Baseline Mock"
    return None


def _resolve_enabled(scaffold_context: dict[str, Any]) -> bool:
    override = scaffold_context.get("enabled")
    if isinstance(override, bool):
        return override
    return _env_flag("PRICE_ENGINE_CORELOGIC_ENABLED")


def _resolve_mode(scaffold_context: dict[str, Any]) -> str:
    override = scaffold_context.get("mode")
    if isinstance(override, str):
        normalized = override.strip().lower()
        if normalized in {CORELOGIC_MODE_DISABLED, CORELOGIC_MODE_MOCK, CORELOGIC_MODE_LIVE}:
            return normalized
    env_mode = os.environ.get("PRICE_ENGINE_CORELOGIC_MODE", "").strip().lower()
    if env_mode in {CORELOGIC_MODE_DISABLED, CORELOGIC_MODE_MOCK, CORELOGIC_MODE_LIVE}:
        return env_mode
    return CORELOGIC_MODE_DISABLED


def _resolve_allow_live_calls(scaffold_context: dict[str, Any]) -> bool:
    override = scaffold_context.get("allowLiveCalls")
    if isinstance(override, bool):
        return override
    return _env_flag("PRICE_ENGINE_CORELOGIC_ALLOW_LIVE_CALLS")


def _resolve_credential_state(scaffold_context: dict[str, Any]) -> str:
    override = scaffold_context.get("credentialPresence")
    if isinstance(override, str):
        normalized = override.strip().lower()
        if normalized in {"missing", "partial", "present"}:
            return normalized

    provided_values = [
        os.environ.get("CORELOGIC_API_BASE_URL", "").strip(),
        os.environ.get("CORELOGIC_CLIENT_ID", "").strip(),
        os.environ.get("CORELOGIC_CLIENT_SECRET", "").strip(),
    ]
    present_count = sum(1 for value in provided_values if value)
    if present_count == 0:
        return "missing"
    if present_count == len(provided_values):
        return "present"
    return "partial"


def _scaffold_context(provider_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(provider_context, dict):
        return {}
    raw = provider_context.get("corelogicScaffold")
    if not isinstance(raw, dict):
        return {}
    return raw


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}
