import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
FUNCTION_ROOT = ROOT / "azure" / "functions" / "asset_ingest"
if str(FUNCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTION_ROOT))

from server.price_engine.providers.corelogic.corelogic_provider import CoreLogicProvider


class CoreLogicScaffoldTests(unittest.TestCase):
    def test_corelogic_provider_returns_deterministic_mock_response(self) -> None:
        response = CoreLogicProvider().get_property_intelligence(
            property_address="123 Main St",
            operator="tester",
        )

        self.assertEqual(response.provider, "corelogic")
        self.assertEqual(response.mode, "mock")
        self.assertEqual(
            response.property_intelligence,
            {
                "AVM": 245000,
                "FloodZone": "X",
                "ParcelId": "MO-JACKSON-000123456",
                "Beds": 3,
                "Baths": 2.0,
                "SqFt": 1680,
                "YearBuilt": 1998,
            },
        )

    def test_corelogic_provider_returns_mock_overlay_payload(self) -> None:
        overlay = CoreLogicProvider().get_property_overlay_payload(
            property_address="1518 Summit Ridge Dr, Kansas City, MO",
            operator="tester",
        )

        self.assertEqual(
            overlay,
            {
                "subject": {
                    "address": "1518 Summit Ridge Dr, Kansas City, MO",
                    "lat": 39.0997,
                    "lng": -94.5786,
                },
                "overlays": {
                    "parcelBoundary": None,
                    "floodZone": {
                        "zone": "X",
                        "panel": "MOCK-1001",
                        "effectiveDate": "2024-01-01",
                    },
                    "corelogicLayerStatus": "mock_ready",
                },
                "propertyIntelligence": {
                    "avm": 245000,
                    "beds": 3,
                    "baths": 2.0,
                    "sqFt": 1680,
                    "yearBuilt": 1998,
                },
                "meta": {
                    "provider": "corelogic",
                    "mock": True,
                    "approvalRequired": True,
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
