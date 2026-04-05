from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUNCTION_APP = ROOT / "azure" / "functions" / "asset_ingest" / "function_app.py"
ROUTE_MAP = ROOT / "docs" / "architecture" / "ROUTE_MAP_V1.md"
COVERAGE_INDEX = ROOT / "docs" / "contracts" / "PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md"
FRONTEND_ENTRYPOINT = ROOT / "docs" / "contracts" / "PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md"

DECORATOR_PATTERN = re.compile(
    r'@app\.route\(route="(?P<route>price-engine/[^"]+)", methods=\[(?P<methods>[^\]]+)\], auth_level=func\.AuthLevel\.ANONYMOUS\)\s*'
    r"def (?P<handler>\w+)\(",
    re.MULTILINE,
)
METHOD_PATTERN = re.compile(r'"([A-Z]+)"')

EXPECTED_ROUTE_HANDLERS = {
    ("POST", "/api/price-engine/calculate", "price_engine_calculate"),
    ("GET", "/api/price-engine/calculations-preview", "price_engine_calculations_preview"),
    ("POST", "/api/price-engine/title-rate-quote", "price_engine_title_rate_quote"),
}


def discover_price_engine_route_handlers() -> set[tuple[str, str, str]]:
    text = FUNCTION_APP.read_text(encoding="utf-8")
    discovered: set[tuple[str, str, str]] = set()
    for match in DECORATOR_PATTERN.finditer(text):
        handler = match.group("handler")
        route = f'/api/{match.group("route")}'
        methods = METHOD_PATTERN.findall(match.group("methods"))
        for method in methods:
            discovered.add((method, route, handler))
    return discovered


class PriceEngineRouteInventoryProofTests(unittest.TestCase):
    def test_live_price_engine_routes_match_expected_handler_inventory(self) -> None:
        self.assertEqual(discover_price_engine_route_handlers(), EXPECTED_ROUTE_HANDLERS)

    def test_route_map_contains_all_live_price_engine_route_rows(self) -> None:
        route_map = ROUTE_MAP.read_text(encoding="utf-8")
        expected_rows = [
            "| POST | `/api/price-engine/calculate` | `price_engine_calculate` | `azure/functions/asset_ingest/function_app.py` | Price engine calculation stub with contract field rounding and failure catalog |",
            "| GET | `/api/price-engine/calculations-preview` | `price_engine_calculations_preview` | `azure/functions/asset_ingest/function_app.py` | Price engine read-only preview surface over query parameters |",
            "| POST | `/api/price-engine/title-rate-quote` | `price_engine_title_rate_quote` | `azure/functions/asset_ingest/function_app.py` | Provider-normalized title quote seam with stub-only runtime behavior |",
        ]
        for row in expected_rows:
            self.assertIn(row, route_map)

    def test_coverage_index_contains_all_live_price_engine_routes(self) -> None:
        coverage_index = COVERAGE_INDEX.read_text(encoding="utf-8")
        for method, route, _ in EXPECTED_ROUTE_HANDLERS:
            self.assertIn(f"`{method} {route}`", coverage_index)

    def test_frontend_entrypoint_contains_all_live_price_engine_routes(self) -> None:
        frontend_entrypoint = FRONTEND_ENTRYPOINT.read_text(encoding="utf-8")
        for method, route, _ in EXPECTED_ROUTE_HANDLERS:
            self.assertIn(f"`{method} {route}`", frontend_entrypoint)


if __name__ == "__main__":
    unittest.main()
