from __future__ import annotations

from decimal import Decimal
from typing import Any


def build_portfolio_summary(portfolio_id: str, as_of: str | None) -> dict[str, Any]:
    seed = sum(ord(character) for character in portfolio_id)
    asset_count = (seed % 18) + 3
    total_units = asset_count * 4
    occupied_units = min(total_units, max(0, total_units - (seed % 7)))
    occupancy_rate = occupied_units / total_units if total_units else 0.0
    estimated_value = Decimal(asset_count) * Decimal("125000.00")

    return {
        "portfolioId": portfolio_id,
        "asOfDate": as_of,
        "assetCount": asset_count,
        "occupiedUnits": occupied_units,
        "totalUnits": total_units,
        "occupancyRate": occupancy_rate,
        "estimatedValue": float(estimated_value),
        "currency": "USD",
        "activeAlerts": seed % 4,
        "status": "stub_ready",
    }
