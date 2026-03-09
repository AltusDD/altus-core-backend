from __future__ import annotations

from typing import Any


def build_asset_search_results(query: str, limit: int, offset: int) -> dict[str, Any]:
    base_seed = sum(ord(character) for character in query)
    total = 8 + (base_seed % 7)
    items: list[dict[str, Any]] = []

    for index in range(offset, min(offset + limit, total)):
        score_seed = ((base_seed + index) % 100) / 100
        items.append(
            {
                "assetId": f"search-asset-{index + 1:03d}",
                "displayName": f"Search Match {index + 1}",
                "address": f"{100 + index} Market Street",
                "match": {
                    "strategy": "name_similarity",
                    "score": min(1.0, max(0.0, round(0.45 + (score_seed / 2), 2))),
                },
                "portfolioId": None,
                "city": None,
                "state": None,
            }
        )

    return {
        "data": items,
        "meta": {
            "query": query,
            "limit": limit,
            "offset": offset,
            "total": total,
        },
    }
