# BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V2

Status: implementation-ready boundary plan
Baseline: draft PR `#86`
Scope: additive planning only for `altus-core-backend`

## Boundary Intent

This note advances the accepted adoption scaffold into the next implementation-ready planning layer without changing routes, response envelopes, migrations, or deployment ownership.

Guardrails:

- no route invention
- no breaking contract changes
- no frontend math embedding
- no queue provider commitment without explicit architecture approval

## Rangekeeper Wrap Boundary

Classification: `wrap`

### Interface Shape

The current safe interface remains the gateway protocol established in `azure/functions/asset_ingest/adoption/pricing_boundary.py`.

Canonical request shape:

- `PricingScenario.scenario_id`
- `PricingScenario.inputs`
- optional engine/version metadata carried as adapter metadata, not as new public route fields
- `PricingRequestContext.correlation_id`
- optional `organization_id`, `actor_id`, and trace headers for audit continuity

Canonical response shape:

- backend returns the existing calculation payload already produced by `calculate_price_engine(...)`
- any future wrapped-service metadata must stay adapter-local unless a contract review explicitly approves an additive response field

### Runtime Placement

`rangekeeper` belongs behind the existing backend calculation seam:

- request handler
- `price_engine_handler.py`
- `price_engine_service.py` or an adjacent adapter module
- gateway implementation selected inside backend runtime

It does not belong:

- in React components
- in chart or table rendering code
- in frontend state machines
- in ad hoc client utilities that bypass the backend contract layer

### Request / Response Boundary Rules

- frontend submits scenario inputs through the existing backend contract
- backend chooses local engine vs wrapped service internally
- response remains the canonical backend calculation result
- transport, retries, and trace metadata stay inside the backend adapter boundary

## Outbox / Writeback Hardening Map

Classification: pattern-only

### Event Source

Candidate event sources for future hardening:

- accepted backend write operations that create follow-on work
- calculation or ingestion completions that require asynchronous downstream notification
- governance-safe writeback requests emitted after canonical data persistence

Request handlers must only create the canonical persistence result plus an outbox record description. They must not perform direct downstream writebacks inline.

### Queue Boundary

The queue boundary begins after a durable outbox record exists. The current scaffold in `azure/functions/asset_ingest/adoption/outbox_boundary.py` defines the minimum envelope:

- `message_id`
- `topic`
- `aggregate_type`
- `aggregate_id`
- `dedupe_key`
- `status`
- `attempt_count`
- `last_error`

Queue provider selection remains deferred. This note only fixes the seam where queue infrastructure would attach.

### Worker Boundary

Workers belong outside the request-serving path and should own:

- dequeue / lease acquisition
- idempotency check against `dedupe_key`
- bounded retry handling
- terminal failure recording
- downstream dispatch to approved writeback integrations

Workers must not redefine route contracts or mutate canonical entities without going through approved backend service modules.

### Audit / Log Boundary

Audit continuity should live in:

- correlation identifiers passed through `PricingRequestContext`
- outbox status / attempt metadata
- structured worker logs keyed by `message_id` and `dedupe_key`
- verification SQL and proof artifacts stored outside request handlers

Request handlers should emit correlation-ready logs, but replay analysis belongs to outbox records plus worker logs, not improvised endpoint behavior.

## Governance / Test Hooks

### Contract-Safe Verification

Contract-safe verification currently lives in:

- `docs/architecture/ROUTE_MAP_V1.md`
- `docs/roadmap/CANONICAL_COMPONENT_ADOPTION_PLAN.md`
- `docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V1.md`
- `docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V2.md`
- `azure/functions/asset_ingest/tests/test_adoption_scaffolds.py`

These surfaces verify that new planning remains additive and keeps the backend wrapper, outbox, and governance seams explicit.

### RLS / Schema Verification

RLS and schema verification should live in:

- `supabase/migrations/` for actual schema or policy changes
- `supabase/verification/` for proof SQL and post-apply verification

It should not live in:

- request handlers
- ad hoc shell scripts attached to runtime paths
- frontend repositories

## Next Implementation Slices

1. Introduce a backend-local adapter selector that can choose the local calculator or a future wrapped pricing service without altering public handlers.
2. Define the durable storage home for outbox records and the exact transaction point where records are created alongside canonical writes.
3. Add worker-oriented replay and retry tests once queue/storage architecture is approved.
4. Add verification SQL for any future RLS/schema work under `supabase/verification/` before policy changes are treated as complete.
5. Keep any future response-shape expansion behind explicit contract review rather than adapter convenience.

## No-Drift Summary

- no route changes
- no response envelope changes
- no migration changes
- no queue provider added
- no frontend responsibility shift
- no direct `rangekeeper` embed
