from __future__ import annotations

from typing import Any

from price_engine_calculations import (
    build_deal_inputs,
    calculate_price_engine_from_inputs,
)
from price_engine_errors import PriceEngineError
from price_engine_disclaimers import build_price_engine_disclaimers
from price_engine_input_normalization import normalize_price_engine_payload
from price_engine_provenance import build_price_engine_provenance
from price_engine_title_quote_mapper import resolve_title_fee_inputs


def calculate_price_engine(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_price_engine_payload(payload)
    base_inputs = build_deal_inputs(normalized.payload)
    title_quote_context = resolve_title_fee_inputs(normalized.payload, base_inputs)
    enriched_payload = dict(normalized.payload)
    enriched_payload.update(title_quote_context.fee_inputs)
    enriched_inputs = build_deal_inputs(enriched_payload)
    result = calculate_price_engine_from_inputs(enriched_inputs)
    result["ScenarioProfile"] = normalized.scenario_profile
    result["AppliedPresetFields"] = normalized.applied_preset_fields
    result["ValidationWarnings"] = normalized.validation_warnings
    result["Disclaimers"] = build_price_engine_disclaimers(
        validation_warnings=normalized.validation_warnings,
        applied_preset_fields=normalized.applied_preset_fields,
        title_quote_provider_key=title_quote_context.provider_key,
        title_quote_status=title_quote_context.status,
    )
    result["Provenance"] = build_price_engine_provenance(
        title_quote_context=title_quote_context,
        scenario_profile=normalized.scenario_profile,
        applied_preset_fields=normalized.applied_preset_fields,
        validation_warnings=normalized.validation_warnings,
    )
    return result


__all__ = ["PriceEngineError", "calculate_price_engine"]
