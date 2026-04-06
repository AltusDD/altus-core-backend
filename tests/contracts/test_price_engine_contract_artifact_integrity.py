from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COVERAGE_INDEX = ROOT / "docs" / "contracts" / "PRICE_ENGINE_CONTRACT_COVERAGE_INDEX_V1.md"
FRONTEND_ENTRYPOINT = ROOT / "docs" / "contracts" / "PRICE_ENGINE_FRONTEND_ENTRYPOINT_V1.md"
ARTIFACT_INTEGRITY_WORKFLOW = ROOT / ".github" / "workflows" / "price_engine_contract_artifact_integrity.yml"
TEST_MODULE = "tests/contracts/test_price_engine_contract_artifact_integrity.py"

EXPECTED_ARTIFACT_PATHS = {
    "docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md",
    "docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md",
    "docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md",
    "docs/contracts/fixtures/price_engine_calculate/",
    "docs/contracts/fixtures/price_engine_calculations_preview/",
    "docs/contracts/fixtures/title_rate_quote/",
    "tests/contracts/test_price_engine_calculate_contract.py",
    "tests/contracts/test_price_engine_contract_proof_integrity.py",
    "tests/contracts/test_price_engine_calculations_preview_contract.py",
    "tests/contracts/test_price_engine_calculations_preview_contract_proof_integrity.py",
    "tests/contracts/test_title_rate_quote_contract.py",
    "tests/contracts/test_title_rate_quote_contract_proof_integrity.py",
    "tests/contracts/test_price_engine_contract_artifact_integrity_proof.py",
    ".github/workflows/price_engine_contract_proof.yml",
    ".github/workflows/price_engine_contract_proof_integrity.yml",
    ".github/workflows/price_engine_calculations_preview_contract_proof.yml",
    ".github/workflows/price_engine_calculations_preview_contract_proof_integrity.yml",
    ".github/workflows/title_rate_quote_contract_proof.yml",
    ".github/workflows/title_rate_quote_contract_proof_integrity.yml",
    ".github/workflows/price_engine_contract_artifact_integrity_proof.yml",
    ".github/workflows/price_engine_proof_gate.yml",
}


def normalize_doc_path(path: str) -> str:
    return path[:-1] if path.endswith("/") else path


class PriceEngineContractArtifactIntegrityTests(unittest.TestCase):
    def test_expected_artifacts_exist_in_repository(self) -> None:
      missing = [
          path
          for path in EXPECTED_ARTIFACT_PATHS
          if not (ROOT / normalize_doc_path(path)).exists()
      ]
      self.assertEqual(missing, [])

    def test_coverage_index_references_all_expected_artifacts(self) -> None:
        text = COVERAGE_INDEX.read_text(encoding="utf-8")
        for artifact_path in EXPECTED_ARTIFACT_PATHS:
            self.assertIn(f"`{artifact_path}`", text)

    def test_frontend_entrypoint_references_all_expected_artifacts(self) -> None:
        text = FRONTEND_ENTRYPOINT.read_text(encoding="utf-8")
        entrypoint_only_paths = {
            "docs/contracts/PRICE_ENGINE_CALCULATE_CONTRACT_V1.md",
            "docs/contracts/PRICE_ENGINE_CALCULATIONS_PREVIEW_CONTRACT_V1.md",
            "docs/contracts/TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1.md",
            "docs/contracts/fixtures/price_engine_calculate/",
            "docs/contracts/fixtures/price_engine_calculations_preview/",
            "docs/contracts/fixtures/title_rate_quote/",
            "tests/contracts/test_price_engine_calculate_contract.py",
            "tests/contracts/test_price_engine_contract_proof_integrity.py",
            "tests/contracts/test_price_engine_calculations_preview_contract.py",
            "tests/contracts/test_price_engine_calculations_preview_contract_proof_integrity.py",
            "tests/contracts/test_title_rate_quote_contract.py",
            "tests/contracts/test_title_rate_quote_contract_proof_integrity.py",
            "tests/contracts/test_price_engine_contract_artifact_integrity_proof.py",
            ".github/workflows/price_engine_contract_proof.yml",
            ".github/workflows/price_engine_contract_proof_integrity.yml",
            ".github/workflows/price_engine_calculations_preview_contract_proof.yml",
            ".github/workflows/price_engine_calculations_preview_contract_proof_integrity.yml",
            ".github/workflows/title_rate_quote_contract_proof.yml",
            ".github/workflows/title_rate_quote_contract_proof_integrity.yml",
            ".github/workflows/price_engine_contract_artifact_integrity_proof.yml",
            ".github/workflows/price_engine_proof_gate.yml",
        }
        for artifact_path in entrypoint_only_paths:
            self.assertIn(f"`{artifact_path}`", text)

    def test_artifact_integrity_workflow_tracks_aggregate_proof_gate(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('".github/workflows/price_engine_proof_gate.yml"', text)

    def test_artifact_integrity_workflow_tracks_route_workflow_integrity_surfaces(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('".github/workflows/price_engine_contract_proof_integrity.yml"', text)
        self.assertIn('".github/workflows/price_engine_calculations_preview_contract_proof_integrity.yml"', text)
        self.assertIn('".github/workflows/title_rate_quote_contract_proof_integrity.yml"', text)
        self.assertIn('".github/workflows/price_engine_contract_artifact_integrity_proof.yml"', text)

    def test_artifact_integrity_workflow_tracks_its_integrity_proof_test(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('"tests/contracts/test_price_engine_contract_artifact_integrity_proof.py"', text)

    def test_artifact_integrity_workflow_writes_proof_gate_summary(self) -> None:
        text = ARTIFACT_INTEGRITY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(TEST_MODULE, text)
        self.assertIn("contract-artifact workflow integrity", text)
        self.assertIn("aggregate proof gate", text)


if __name__ == "__main__":
    unittest.main()
