from __future__ import annotations

from typing import Any


def build_asset_metrics(asset_id: str, window_days: int) -> dict[str, Any]:
    seed = sum(ord(character) for character in asset_id)
    occupancy_rate = ((seed % 61) + 20) / 100
    maintenance_ratio = ((seed % 18) + 5) / 100
    collections_ratio = ((seed % 10) + 90) / 100

    return {
        "assetId": asset_id,
        "windowDays": window_days,
        "occupancyRate": round(min(1.0, max(0.0, occupancy_rate)), 2),
        "maintenanceCostRatio": round(min(1.0, max(0.0, maintenance_ratio)), 2),
        "collectionsRate": round(min(1.0, max(0.0, collections_ratio)), 2),
        "delinquentUnits": seed % 5,
        "openWorkOrders": seed % 7,
        "netOperatingIncome": float((seed % 90 + 10) * 1000),
        "currency": "USD",
        "lastUpdatedAt": None,
    }
