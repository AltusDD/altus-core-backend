import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from title_rate_liberty_snapshot import normalize_liberty_quote_snapshot  # noqa: E402


class LibertyQuoteSnapshotNormalizationTests(unittest.TestCase):
    def test_normalizes_canonical_snapshot_shape(self) -> None:
        snapshot = normalize_liberty_quote_snapshot(
            {
                "requestedProvider": "liberty",
                "libertySnapshot": {
                    "quoteReference": "LIA-QUOTE-001",
                    "snapshotVersion": "v1",
                    "quotedAt": "2026-03-18T15:45:00Z",
                    "capturedAt": "2026-03-18T15:46:00Z",
                    "source": "liberty_iframe_snapshot",
                    "expiresAt": "2026-03-19T00:00:00Z",
                    "fees": {
                        "titlePremium": 1800,
                        "settlementFee": 850,
                        "recordingFee": 225,
                        "ownerPolicy": 450,
                        "lenderPolicy": 375,
                    },
                },
            }
        )

        self.assertEqual(snapshot.quote_reference, "LIA-QUOTE-001")
        self.assertEqual(snapshot.snapshot_version, "v1")
        self.assertEqual(snapshot.source, "liberty_iframe_snapshot")
        self.assertEqual(str(snapshot.title_premium), "1800.00")
        self.assertEqual(str(snapshot.settlement_fee), "850.00")

    def test_normalizes_legacy_quote_shape(self) -> None:
        snapshot = normalize_liberty_quote_snapshot(
            {
                "requestedProvider": "liberty",
                "libertyQuote": {
                    "quoteReference": "LIA-LEGACY-001",
                    "titlePremium": 1800,
                    "settlementServices": 850,
                    "recordingFees": 225,
                    "ownerPolicy": 450,
                    "lenderPolicy": 375,
                },
            }
        )

        self.assertEqual(snapshot.quote_reference, "LIA-LEGACY-001")
        self.assertEqual(snapshot.snapshot_version, "legacy-v0")
        self.assertEqual(snapshot.source, "liberty_iframe_snapshot_legacy")
        self.assertEqual(str(snapshot.recording_fee), "225.00")

    def test_invalid_snapshot_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            normalize_liberty_quote_snapshot(
                {
                    "requestedProvider": "liberty",
                    "libertySnapshot": {
                        "quoteReference": "LIA-BAD-001",
                        "fees": {
                            "titlePremium": -1,
                            "settlementFee": 850,
                            "recordingFee": 225,
                            "ownerPolicy": 450,
                            "lenderPolicy": 375,
                        },
                    },
                }
            )


if __name__ == "__main__":
    unittest.main()
