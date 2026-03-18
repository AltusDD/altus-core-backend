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
    artifact_type: str | None
    artifact_id: str | None
    trace_key: str | None
    event_type: str | None
    event_ref: str | None
    mock_profile: str | None
    mock_profile_label: str | None
    mock_payload: dict[str, Any] | None


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
    credentials_present = _resolve_credentials_present(scaffold_context)

    if not enabled:
        return _build_scaffold(
            mode=CORELOGIC_MODE_DISABLED if mode == CORELOGIC_MODE_DISABLED else mode,
            state=CORELOGIC_STATE_INACTIVE,
            reason_codes=["integration_disabled", "mode_disabled"] if mode == CORELOGIC_MODE_DISABLED else ["integration_disabled"],
            mock_payload=None,
        )

    if mode == CORELOGIC_MODE_DISABLED:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_INACTIVE,
            reason_codes=["mode_disabled"],
            mock_payload=None,
        )

    if mode == CORELOGIC_MODE_MOCK:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_MOCK_READY,
            reason_codes=["mode_mock"],
            mock_payload=_build_mock_payload(),
        )

    if not allow_live_calls:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_LIVE_BLOCKED,
            reason_codes=["live_calls_not_allowed", "live_mode_enabled"],
            mock_payload=None,
        )

    if not credentials_present:
        return _build_scaffold(
            mode=mode,
            state=CORELOGIC_STATE_LIVE_BLOCKED,
            reason_codes=["live_credentials_missing", "live_mode_enabled"],
            mock_payload=None,
        )

    return _build_scaffold(
        mode=mode,
        state=CORELOGIC_STATE_LIVE_READY,
        reason_codes=["live_mode_enabled"],
        mock_payload=None,
    )


def _build_scaffold(
    *,
    mode: str,
    state: str,
    reason_codes: list[str],
    mock_payload: dict[str, Any] | None,
) -> CoreLogicIntegrationScaffold:
    return CoreLogicIntegrationScaffold(
        provider=CORELOGIC_PROVIDER_KEY,
        mode=mode,
        state=state,
        state_label=_build_state_label(state),
        reason_codes=_ordered_unique_reason_codes(reason_codes),
        artifact_type=_build_artifact_type(mode),
        artifact_id=_build_artifact_id(mode),
        trace_key=_build_trace_key(mode),
        event_type=_build_event_type(mode),
        event_ref=_build_event_ref(mode),
        mock_profile=_build_mock_profile(mode),
        mock_profile_label=_build_mock_profile_label(mode),
        mock_payload=mock_payload,
    )


def _build_state_label(state: str) -> str:
    if state == CORELOGIC_STATE_MOCK_READY:
        return "Mock Integration Ready"
    if state == CORELOGIC_STATE_LIVE_BLOCKED:
        return "Live Integration Blocked"
    if state == CORELOGIC_STATE_LIVE_READY:
        return "Live Integration Ready"
    return "Integration Inactive"


def _ordered_unique_reason_codes(reason_codes: list[str]) -> list[str]:
    reason_code_set = set(reason_codes)
    return [code for code in _REASON_CODE_ORDER if code in reason_code_set]


def _build_mock_payload() -> dict[str, Any]:
    return {
        "provider": CORELOGIC_PROVIDER_KEY,
        "mode": CORELOGIC_MODE_MOCK,
        "state": CORELOGIC_STATE_MOCK_READY,
        "propertyOverlay": "mock_static",
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


def _resolve_credentials_present(scaffold_context: dict[str, Any]) -> bool:
    override = scaffold_context.get("credentialsPresent")
    if isinstance(override, bool):
        return override
    api_key = os.environ.get("PRICE_ENGINE_CORELOGIC_API_KEY", "").strip()
    client_id = os.environ.get("PRICE_ENGINE_CORELOGIC_CLIENT_ID", "").strip()
    return bool(api_key or client_id)


def _scaffold_context(provider_context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(provider_context, dict):
        return {}
    raw = provider_context.get("corelogicScaffold")
    if not isinstance(raw, dict):
        return {}
    return raw


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}
