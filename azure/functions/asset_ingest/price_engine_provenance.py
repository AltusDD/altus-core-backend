from __future__ import annotations

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

    return {
        "titleQuote": {
            "provider": provider,
            "status": status,
            "source": source,
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
