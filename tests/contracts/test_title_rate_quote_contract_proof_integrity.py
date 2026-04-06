from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "title_rate_quote_contract_proof.yml"

EXPECTED_PATHS = [
    "tests/contracts/test_title_rate_quote_contract.py",
    "docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md",
    "docs/contracts/PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md",
    "docs/contracts/fixtures/title_rate_quote/**",
    "docs/architecture/ROUTE_MAP_V1.md",
    "azure/functions/asset_ingest/title_rate_handler.py",
    "azure/functions/asset_ingest/title_rate_provider.py",
    ".github/workflows/title_rate_quote_contract_proof.yml",
]


class TitleRateQuoteContractProofIntegrityTests(unittest.TestCase):
    def test_workflow_tracks_expected_title_rate_dependencies(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        for path in EXPECTED_PATHS:
            self.assertIn(path, text)

    def test_workflow_runs_expected_test_module(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_title_rate_quote_contract.py", text)

    def test_workflow_writes_route_and_provider_summary(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("TITLE RATE QUOTE CONTRACT PROOF", text)
        self.assertIn("POST /api/price-engine/title-rate-quote", text)
        self.assertIn("provider-normalized title quote seam", text)
        self.assertIn("PRICE_ENGINE_TITLE_RATE_PROVIDER", text)


if __name__ == "__main__":
    unittest.main()
