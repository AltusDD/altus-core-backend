# BACKEND_ADOPTION_MERGE_READINESS_NOTE

Status: merge-readiness summary for accepted backend adoption sequence
Baseline PRs: `#86`, `#87`

## Sequence Summary

| PR | Established |
| --- | --- |
| `#86` | Canonical roadmap, implementation note v1, pricing wrapper scaffold, outbox scaffold, governance hooks, and proof tests without changing routes, contracts, or migrations. |
| `#87` | Implementation note v2 with implementation-ready wrapper boundary, outbox/writeback hardening map, governance verification placement, and next execution slices. |

## Dependency / Pattern Classification

| Item | Classification | State |
| --- | --- | --- |
| `rangekeeper` | `wrap` | deferred behind backend adapter boundary |
| `ts-to-rls-demo` concepts | `pattern-only` | adopted as governance workflow reference |
| outbox pattern | `pattern-only` | adopted as scaffold and execution map |
| `supabase-management-js` | `deferred` | not architecture-fit for current Python runtime |

## Still Deferred

- live `rangekeeper` adapter implementation
- durable outbox storage choice
- queue provider / worker runtime choice
- RLS or schema migration work
- any route or response-envelope expansion

## Next Implementation Slices

1. Add a backend-local adapter selector that chooses local calculator vs future wrapped pricing service.
2. Define the durable outbox persistence point alongside canonical writes.
3. Introduce worker-side retry/replay handling after queue/storage approval.
4. Add `supabase/verification/` SQL for any future schema or RLS changes before execution work is treated as complete.
5. Keep response-shape or contract changes behind separate explicit review.

## Scope Guardrails

- no route changes
- no contract changes
- no migration changes
- no deployment retargeting
