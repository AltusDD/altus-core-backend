from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PriceEngineTitleQuoteContext:
    fee_inputs: dict[str, float]
    provider_key: str | None
    status: str | None
    quote_reference: str | None
    expires_at: str | None
    warnings: list[str]
    assumptions: list[str]
    provider_context: dict[str, Any]
