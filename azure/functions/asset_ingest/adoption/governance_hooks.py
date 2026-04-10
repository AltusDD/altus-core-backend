from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernanceCheck:
    name: str
    path: str
    reason: str


def build_governance_checks() -> list[GovernanceCheck]:
    return [
        GovernanceCheck(
            name="route-map",
            path="docs/architecture/ROUTE_MAP_V1.md",
            reason="No route additions or route drift are allowed without explicit route-map updates.",
        ),
        GovernanceCheck(
            name="canonical-roadmap",
            path="docs/roadmap/CANONICAL_COMPONENT_ADOPTION_PLAN.md",
            reason="This adoption branch must stay aligned with the canonical component plan committed in-repo.",
        ),
        GovernanceCheck(
            name="implementation-note",
            path="docs/architecture/BACKEND_ADOPTION_IMPLEMENTATION_NOTE_V1.md",
            reason="Adoption classification and deferrals must be documented in a repo-local proof note.",
        ),
        GovernanceCheck(
            name="verification-sql-home",
            path="supabase/verification/README.md",
            reason="Schema and RLS proof belongs in the verification SQL surface, not in ad hoc handler logic.",
        ),
    ]
