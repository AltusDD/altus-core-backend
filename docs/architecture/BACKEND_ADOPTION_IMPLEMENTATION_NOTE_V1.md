# BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V1

Status: proof-ready implementation note for canonical component adoption
Scope: `altus-core-backend` on `feature/canonical-component-adoption`

## Current Architecture Fit

- Runtime: Python Azure Functions in `azure/functions/asset_ingest/`
- Deployment model: Azure Functions with Managed Identity + Key Vault secret resolution in the request-serving app
- Current price engine boundary: `function_app.py` -> `price_engine_handler.py` -> `price_engine_service.py`
- Current schema governance surface: SQL migrations in `supabase/migrations/`
- Current repo does not expose a committed Node runtime or package-manager surface for backend execution

## Adopted Vs Deferred

| Item | Classification | Status | Why | Intended surface |
| --- | --- | --- | --- | --- |
| `rangekeeper` | `wrap` | adopted as scaffold | Backend math must remain behind a service boundary. This repo already has a price-engine seam, so the safe move is a wrapper interface, not direct embed. | `azure/functions/asset_ingest/adoption/pricing_boundary.py` |
| `ts-to-rls-demo` | `pattern-only` | adopted as governance concept | The concept fits governance review, but this repo is Python + SQL and does not justify importing TypeScript tooling directly. | `docs/architecture/`, `supabase/verification/` |
| `nodejs-outbox pattern` | `pattern-only` | adopted as scaffold | Outbox durability and replay safety are useful here, but the Node implementation is not architecture-fit. Only the pattern is extracted. | `azure/functions/asset_ingest/adoption/outbox_boundary.py` |
| `supabase-management-js` | `deferred` | deferred | The current backend runtime is not a Node admin service. Installing this now would create repo drift without a valid execution boundary. | future admin-only governance tool, outside request path |
| Microsoft Graph Toolkit concepts | `deferred` | deferred / out of scope | Not a backend runtime dependency and explicitly outside FE/BE confusion for this repo. | none |

## Dependency Outcome

No dependency changes were made.

Reason:

- `azure/functions/asset_ingest/requirements.txt` is the active runtime dependency surface.
- None of the approved Node-specific items are confirmed architecture-fit for this Python Functions repo.
- Safe progress here comes from wrapper notes, governance hooks, and queue contracts, not blind installs.

## Pricing Service Wrapper Boundary

Added:

- `azure/functions/asset_ingest/adoption/pricing_boundary.py`

Purpose:

- Preserve the current calculation contract while creating a stable gateway for future wrapped pricing engines
- Keep local `price_engine_service.calculate_price_engine(...)` as the default path
- Make any future `rangekeeper` adoption opt-in and adapter-based

Guardrails:

- No route changes
- No request/response envelope changes
- No math engine logic moved into handlers

## Event Bus / Writeback / Outbox Hardening Note

Added:

- `azure/functions/asset_ingest/adoption/outbox_boundary.py`

Purpose:

- Define a durable outbox envelope with `message_id`, `dedupe_key`, `attempt_count`, and replay/error fields
- Create a backend-safe record format before choosing queue infrastructure
- Keep queue selection, storage persistence, and dispatch workers deferred until architecture review

Guardrails:

- No storage migration added in this change
- No background runner added in this change
- No endpoint behavior changed in this change

## RLS / Schema Governance Workflow Note

Added:

- `azure/functions/asset_ingest/adoption/governance_hooks.py`
- `supabase/verification/README.md`

Purpose:

- Make route, schema, and verification authority explicit before future backend expansion
- Establish the correct home for post-apply SQL verification without pretending the workflow is fully automated on this branch

Governance rule:

- Schema or RLS changes belong in `supabase/migrations/`
- Proof-style verification SQL belongs in `supabase/verification/`
- Request-serving handlers must not become the place where governance checks are improvised

## Safe Scaffolds Added

| Surface | Files |
| --- | --- |
| Canonical roadmap | `docs/roadmap/CANONICAL_COMPONENT_ADOPTION_PLAN.md` |
| Implementation note | `docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V1.md` |
| Pricing wrapper scaffold | `azure/functions/asset_ingest/adoption/pricing_boundary.py` |
| Outbox scaffold | `azure/functions/asset_ingest/adoption/outbox_boundary.py` |
| Governance hooks | `azure/functions/asset_ingest/adoption/governance_hooks.py` |
| Governance verification placeholder docs | `supabase/verification/README.md` |
| Proof test | `azure/functions/asset_ingest/tests/test_adoption_scaffolds.py` |

## Explicitly Deferred

- Live `rangekeeper` integration
- Any direct `supabase-management-js` installation
- Queue provider selection
- New migrations, policies, routes, or contract fields
- Any backend embedding of external math service internals

## Rollback

This change is reversible by removing:

- `docs/roadmap/CANONICAL_COMPONENT_ADOPTION_PLAN.md`
- `docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V1.md`
- `azure/functions/asset_ingest/adoption/`
- `azure/functions/asset_ingest/tests/test_adoption_scaffolds.py`
- `supabase/verification/README.md`

No contract rollback, route rollback, migration rollback, or deployment retargeting is required.
