from __future__ import annotations

from typing import Any

from price_engine_calculations import (
    build_deal_inputs,
    calculate_price_engine_from_inputs,
)
from price_engine_errors import PriceEngineError
from price_engine_input_normalization import normalize_price_engine_payload
from price_engine_title_quote_mapper import enrich_payload_with_title_quote


def calculate_price_engine(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_price_engine_payload(payload)
    base_inputs = build_deal_inputs(normalized.payload)
    enriched_payload = enrich_payload_with_title_quote(normalized.payload, base_inputs)
    enriched_inputs = build_deal_inputs(enriched_payload)
    result = calculate_price_engine_from_inputs(enriched_inputs)
    result["ScenarioProfile"] = normalized.scenario_profile
    result["AppliedPresetFields"] = normalized.applied_preset_fields
    result["ValidationWarnings"] = normalized.validation_warnings
    return result


__all__ = ["PriceEngineError", "calculate_price_engine"]
