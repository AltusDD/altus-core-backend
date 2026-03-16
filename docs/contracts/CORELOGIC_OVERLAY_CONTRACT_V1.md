# CORELOGIC_OVERLAY_CONTRACT_V1

Status: draft, mock-safe only  
Scope: Price Engine property intelligence and map overlay docking surface  
Live paid provider calls: not authorized in this contract slice

## Purpose

This contract defines the backend-ready payload shape the Price Engine frontend can use to dock:

- subject property map coordinates
- parcel boundary placeholder data
- flood zone overlay placeholder data
- normalized property intelligence values
- provider/source metadata

This contract is mock-safe and additive. It does not change the existing Price Engine calculate contract.

## Response Shape

```json
{
  "subject": {
    "address": "string",
    "lat": 0,
    "lng": 0
  },
  "overlays": {
    "parcelBoundary": null,
    "floodZone": null,
    "corelogicLayerStatus": "string"
  },
  "propertyIntelligence": {
    "avm": null,
    "beds": null,
    "baths": null,
    "sqFt": null,
    "yearBuilt": null
  },
  "meta": {
    "provider": "string",
    "mock": true,
    "approvalRequired": true
  }
}
```

## Field Notes

- `subject.address`: normalized display address for the mapped subject property.
- `subject.lat` / `subject.lng`: frontend-ready coordinates for map centering and pin placement.
- `overlays.parcelBoundary`: `null` until approved provider geometry is available; later may hold polygon or multipolygon data.
- `overlays.floodZone`: `null` until approved overlay data is available; later may hold zone metadata and geometry references.
- `overlays.corelogicLayerStatus`: quick provider state signal for UI overlay controls.
- `propertyIntelligence`: normalized property facts the frontend can display without vendor-specific field names.
- `meta.provider`: current provider identity, expected to be `corelogic` for this surface.
- `meta.mock`: explicit indicator that this payload is deterministic mock data.
- `meta.approvalRequired`: explicit guardrail indicator that live paid provider activation still requires operator approval.

## Mock Notes

- This contract is currently satisfied by deterministic mock payload generation only.
- No live CoreLogic request is permitted through this surface.
- Parcel boundary and flood geometry remain placeholders until provider approval and implementation are authorized.
