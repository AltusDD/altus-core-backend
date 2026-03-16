from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreLogicPropertyIntelligence:
    avm: int
    flood_zone: str
    parcel_id: str
    beds: int
    baths: float
    sqft: int
    year_built: int

    def to_dict(self) -> dict[str, object]:
        return {
            "AVM": self.avm,
            "FloodZone": self.flood_zone,
            "ParcelId": self.parcel_id,
            "Beds": self.beds,
            "Baths": self.baths,
            "SqFt": self.sqft,
            "YearBuilt": self.year_built,
        }


@dataclass(frozen=True)
class SubjectProperty:
    address: str
    lat: float
    lng: float

    def to_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
        }


@dataclass(frozen=True)
class PropertyOverlayState:
    parcel_boundary: dict[str, object] | None
    flood_zone: dict[str, object] | None
    corelogic_layer_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "parcelBoundary": self.parcel_boundary,
            "floodZone": self.flood_zone,
            "corelogicLayerStatus": self.corelogic_layer_status,
        }


@dataclass(frozen=True)
class NormalizedPropertyIntelligence:
    avm: int | None
    beds: int | None
    baths: float | None
    sqft: int | None
    year_built: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "avm": self.avm,
            "beds": self.beds,
            "baths": self.baths,
            "sqFt": self.sqft,
            "yearBuilt": self.year_built,
        }


@dataclass(frozen=True)
class OverlayMeta:
    provider: str
    mock: bool
    approval_required: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "mock": self.mock,
            "approvalRequired": self.approval_required,
        }


@dataclass(frozen=True)
class CoreLogicOverlayPayload:
    subject: SubjectProperty
    overlays: PropertyOverlayState
    property_intelligence: NormalizedPropertyIntelligence
    meta: OverlayMeta

    def to_dict(self) -> dict[str, object]:
        return {
            "subject": self.subject.to_dict(),
            "overlays": self.overlays.to_dict(),
            "propertyIntelligence": self.property_intelligence.to_dict(),
            "meta": self.meta.to_dict(),
        }


def mock_property_intelligence() -> CoreLogicPropertyIntelligence:
    return CoreLogicPropertyIntelligence(
        avm=245000,
        flood_zone="X",
        parcel_id="MO-JACKSON-000123456",
        beds=3,
        baths=2.0,
        sqft=1680,
        year_built=1998,
    )


def mock_overlay_payload(*, property_address: str) -> CoreLogicOverlayPayload:
    property_intelligence = mock_property_intelligence()
    return CoreLogicOverlayPayload(
        subject=SubjectProperty(
            address=property_address,
            lat=39.0997,
            lng=-94.5786,
        ),
        overlays=PropertyOverlayState(
            parcel_boundary=None,
            flood_zone={
                "zone": property_intelligence.flood_zone,
                "panel": "MOCK-1001",
                "effectiveDate": "2024-01-01",
            },
            corelogic_layer_status="mock_ready",
        ),
        property_intelligence=NormalizedPropertyIntelligence(
            avm=property_intelligence.avm,
            beds=property_intelligence.beds,
            baths=property_intelligence.baths,
            sqft=property_intelligence.sqft,
            year_built=property_intelligence.year_built,
        ),
        meta=OverlayMeta(
            provider="corelogic",
            mock=True,
            approval_required=True,
        ),
    )
