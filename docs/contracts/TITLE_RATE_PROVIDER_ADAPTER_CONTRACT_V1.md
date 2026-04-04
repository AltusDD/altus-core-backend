# TITLE_RATE_PROVIDER_ADAPTER_CONTRACT_V1

Status: Additive provider seam baseline
Route: `POST /api/price-engine/title-rate-quote`
Runtime owner: `azure/functions/asset_ingest/title_rate_handler.py`

This document records the normalized provider adapter contract for title-rate quoting in Price Engine. It introduces a vendor-neutral request and response seam while keeping unsafe vendor automation out of the backend.

## Scope Boundary

- This contract is additive and does not change `/api/price-engine/calculate`.
- This contract does not implement third-party scraping, browser automation, or headless browsing.
- The public Liberty iframe currently exposes a tokenized app launch rather than a documented server-to-server quote API.
- This contract allows provider selection through configuration and supports a deterministic Liberty quote snapshot ingest path plus the stub provider.

## Provider Selection

- Environment variable: `PRICE_ENGINE_TITLE_RATE_PROVIDER`
- Supported values in this slice:
  - `stub`
  - `liberty`
- Explicit unsupported behaviors:
  - missing env var -> `TITLE_RATE_PROVIDER_NOT_CONFIGURED`
  - unknown provider key -> `UNSUPPORTED_TITLE_RATE_PROVIDER`

## Normalized Request Shape

Status code:
- `200` when a configured provider responds successfully
- `400` for validation failures
- `501` when no approved provider is configured or when the configured provider is unsupported

Request body:

```json
{
  "transactionType": "purchase",
  "propertyState": "MO",
  "county": "Jackson",
  "city": "Kansas City",
  "postalCode": "64108",
  "salesPrice": 425000,
  "loanAmount": 300000,
  "ownerPolicyAmount": 425000,
  "lenderPolicyAmount": 300000,
  "endorsements": ["CPL", "T-19"],
  "transactionDate": "2026-03-14",
  "providerContext": {
    "requestedProvider": "liberty",
    "libertySnapshot": {
      "quoteReference": "LIA-QUOTE-001",
      "snapshotVersion": "v1",
      "quotedAt": "2026-03-18T15:45:00Z",
      "capturedAt": "2026-03-18T15:46:00Z",
      "source": "liberty_iframe_snapshot",
      "expiresAt": "2026-03-19T00:00:00Z",
      "fees": {
        "titlePremium": 1800.0,
        "settlementFee": 850.0,
        "recordingFee": 225.0,
        "ownerPolicy": 450.0,
        "lenderPolicy": 375.0
      }
    }
  }
}
```

## Request Fields

- `transactionType` required: `purchase|refinance|sale`
- `propertyState` required: 2-letter state code
- `county` optional
- `city` optional
- `postalCode` optional
- `salesPrice` required numeric
- `loanAmount` optional numeric, defaults to `0`
- `ownerPolicyAmount` optional numeric, defaults to `salesPrice`
- `lenderPolicyAmount` optional numeric, defaults to `loanAmount`
- `endorsements` optional array of strings
- `transactionDate` optional string
- `providerContext` optional object for provider-specific metadata
- `providerContext.libertySnapshot` optional approved quote snapshot ingest object when `PRICE_ENGINE_TITLE_RATE_PROVIDER=liberty`
- `providerContext.libertySnapshot.quoteReference` required for traceability
- `providerContext.libertySnapshot.snapshotVersion` optional string, defaults to `v1`
- `providerContext.libertySnapshot.quotedAt` optional string
- `providerContext.libertySnapshot.capturedAt` optional string
- `providerContext.libertySnapshot.source` optional string, defaults to `liberty_iframe_snapshot`
- `providerContext.libertySnapshot.expiresAt` optional string
- `providerContext.libertySnapshot.fees.titlePremium` maps to canonical `titlePremium`
- `providerContext.libertySnapshot.fees.settlementFee` or `settlementServices` maps to canonical `settlementFee`
- `providerContext.libertySnapshot.fees.recordingFee` or `recordingFees` maps to canonical `recordingFee`
- `providerContext.libertySnapshot.fees.ownerPolicy` maps to canonical `ownerPolicy`
- `providerContext.libertySnapshot.fees.lenderPolicy` maps to canonical `lenderPolicy`
- Legacy `providerContext.libertyQuote` remains accepted as a backward-compatible alias and is normalized to snapshot version `legacy-v0`

## Normalized Success Response Shape

```json
{
  "providerKey": "liberty",
  "status": "quoted",
  "quoteReference": "LIA-QUOTE-001",
  "totals": {
    "ownerPolicy": 450.0,
    "lenderPolicy": 375.0,
    "endorsements": 0.0,
    "settlementServices": 850.0,
    "recordingFees": 225.0,
    "transferTaxes": 0.0,
    "otherFees": 1800.0,
    "total": 3700.0
  },
  "lineItems": [
    {
      "code": "title-premium",
      "category": "policy",
      "description": "Liberty title premium",
      "amount": 1800.0
    }
  ],
  "assumptions": [
    "Liberty quote values were supplied through the approved quote snapshot ingest path."
  ],
  "warnings": [
    "Liberty public iframe currently exposes a tokenized app launch rather than a documented backend quote API."
  ],
  "expiresAt": "2026-03-19T00:00:00Z",
  "providerContext": {
    "mode": "snapshot_ingest",
    "requestedProvider": "liberty",
    "source": "liberty_iframe_snapshot",
    "snapshotVersion": "v1",
    "quotedAt": "2026-03-18T15:45:00Z",
    "capturedAt": "2026-03-18T15:46:00Z",
    "automationAvailable": false
  }
}
```

## Response Fields

- `providerKey`
- `status`
- `quoteReference`
- `totals.ownerPolicy`
- `totals.lenderPolicy`
- `totals.endorsements`
- `totals.settlementServices`
- `totals.recordingFees`
- `totals.transferTaxes`
- `totals.otherFees`
- `totals.total`
- `lineItems[]`
- `lineItems[].code`
- `lineItems[].category`
- `lineItems[].description`
- `lineItems[].amount`
- `assumptions[]`
- `warnings[]`
- `expiresAt`
- `providerContext`

## Error Contract

Response shape:

```json
{
  "error": {
    "code": "TITLE_RATE_PROVIDER_NOT_CONFIGURED",
    "message": "human readable message",
    "details": null
  }
}
```

Named error codes in this slice:
- `VALIDATION_FAILED`
- `TITLE_RATE_PROVIDER_NOT_CONFIGURED`
- `UNSUPPORTED_TITLE_RATE_PROVIDER`
- `INTERNAL_ERROR`

## Proof Fixtures

The proof-bearing fixtures for this route live under:

- `docs/contracts/fixtures/title_rate_quote/stub_request.json`
- `docs/contracts/fixtures/title_rate_quote/stub_response.json`
- `docs/contracts/fixtures/title_rate_quote/liberty_request.json`
- `docs/contracts/fixtures/title_rate_quote/liberty_response.json`
- `docs/contracts/fixtures/title_rate_quote/error_no_provider_request.json`
- `docs/contracts/fixtures/title_rate_quote/error_no_provider_response.json`

## Proof Rules

- If the normalized request or response contract changes, fixtures and tests must change in the same PR.
- Vendor-specific fields must remain isolated inside `providerContext` unless promoted intentionally in a future additive revision.
- Liberty quote retrieval currently depends on an approved quote snapshot ingest path because the public iframe does not expose a documented backend quote API in this build.
- A non-snapshot Liberty automation path must not be added without explicit approval and updated proof fixtures.
