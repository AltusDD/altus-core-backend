from __future__ import annotations

from typing import Any


def build_portfolio_assets(portfolio_id: str, limit: int, offset: int) -> dict[str, Any]:
    base_seed = sum(ord(character) for character in portfolio_id)
    total = 12 + (base_seed % 9)
    rows: list[dict[str, Any]] = []

    for index in range(offset, min(offset + limit, total)):
        units = 4 + ((base_seed + index) % 8)
        occupied_units = max(0, units - ((base_seed + index) % 3))
        rows.append(
            {
                "assetId": f"{portfolio_id}-asset-{index + 1:03d}",
                "portfolioId": portfolio_id,
                "displayName": f"Portfolio Asset {index + 1}",
                "assetType": "multifamily",
                "status": "stub_ready",
                "occupiedUnits": occupied_units,
                "totalUnits": units,
                "occupancyRate": occupied_units / units if units else 0.0,
                "marketValue": float((index + 1) * 100000),
                "city": None,
                "state": None,
            }
        )

    return {
        "data": rows,
        "meta": {
            "portfolioId": portfolio_id,
            "limit": limit,
            "offset": offset,
            "total": total,
        },
    }
