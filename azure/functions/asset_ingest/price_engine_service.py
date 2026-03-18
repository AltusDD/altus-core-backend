from __future__ import annotations

from typing import Any

from price_engine_calculations import (
    PriceEngineError,
    build_deal_inputs,
    calculate_price_engine_from_inputs,
)
from price_engine_title_quote_mapper import enrich_payload_with_title_quote


def calculate_price_engine(payload: dict[str, Any]) -> dict[str, Any]:
    base_inputs = build_deal_inputs(payload)
    enriched_payload = enrich_payload_with_title_quote(payload, base_inputs)
    enriched_inputs = build_deal_inputs(enriched_payload)
    return calculate_price_engine_from_inputs(enriched_inputs)


__all__ = ["PriceEngineError", "calculate_price_engine"]
