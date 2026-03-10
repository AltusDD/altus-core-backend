from __future__ import annotations

from typing import Any


def build_system_health() -> dict[str, Any]:
    return {
        "status": "operational",
        "generatedAt": None,
        "components": [
            {"name": "assetIndex", "status": "operational", "latencyMs": 42, "details": None},
            {"name": "portfolioCache", "status": "operational", "latencyMs": 18, "details": None},
            {"name": "priceEngine", "status": "degraded", "latencyMs": 64, "details": None},
        ],
        "activeIncidents": 1,
    }
