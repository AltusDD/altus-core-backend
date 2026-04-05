from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_README = ROOT / "docs" / "contracts" / "README.md"

EXPECTED_PRICE_ENGINE_REFERENCES = [
    "docs/contracts/PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    ".github/workflows/price_engine_proof_gate.yml",
]


class PriceEngineContractsReadmeIntegrityTests(unittest.TestCase):
    def test_contracts_readme_contains_price_engine_discovery_references(self) -> None:
        text = CONTRACTS_README.read_text(encoding="utf-8")
        for path in EXPECTED_PRICE_ENGINE_REFERENCES:
            self.assertIn(f"`{path}`", text)


if __name__ == "__main__":
    unittest.main()
