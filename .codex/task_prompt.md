You are Codex running in GitHub Actions for Altus-Realty-Group/altus-core-backend.

Operate in non-interactive CI mode.
Complete the GitHub issue using the smallest additive change set that satisfies the request.
Keep edits grounded in this backend repository's actual routes, data surfaces, docs, and workflows.
Do not change deploy targets, runtime secrets, or production handlers unless the issue explicitly requires it.
Do not invent routes, data contracts, or environment behavior. If the issue is underspecified, make the safest reasonable assumption and document it in the final summary.

Issue number: 31
Issue URL: https://github.com/Altus-Realty-Group/altus-core-backend/issues/31
Execution class: docs
Labels JSON: ["lane:be-core","status:queued","docs"]

Issue title:
[DB] Schema inventory truth baseline

Issue body:
## Target environment
staging

## Database type
supabase-postgres

## Target project/ref
SUPABASE_STAGING_PROJECT_REF

## Affected tables/views/functions/policies
- table public.organizations
- table public.profiles
- table public.organization_members
- table public.assets
- table public.asset_data_raw
- table public.asset_specs_reconciled
- function public._touch_updated_at()
- function public.altus_current_org_id()
- function public.altus_is_org_member(uuid)
- function public.altus_login(text)
- function public.altus_me()
- function public.altus_logout()
- policies from 0002_altus_core_identity.sql
- policy assets_org_isolation from supabase/policies/rls_enterprise_asset_master.sql

## Migration required?
no

## Verification query required?
yes

## Rollback note
Revert the schema inventory documentation and verification SQL if the inventory needs to be redrafted; no live schema mutation is part of this task.

## Risk class
low

## Contract/doc update required?
yes

## Acceptance criteria
- docs/database/SCHEMA_INVENTORY_V1.md documents repo-proven critical schema surfaces
- DATA_MAP_V1 calls out repo-proven schema caveats and unproven code expectations
- docs/contracts/README.md points to the schema inventory as current inventory authority
- non-destructive verification SQL exists for schema inventory inspection
- unknowns are explicitly labeled without inventing live state

## Unknowns / assumptions
- Live staging may contain columns or objects not proven by repository migrations on main.
- Historical proof artifacts reference docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md, but that file is not present on main.
- asset_links and several runtime-expected columns are treated as unproven until verified in a later staged inspection.


Required deliverables:
- Make the requested repository changes.
- Leave the repo in a state suitable for a pull request.
- Summarize what changed, what validation ran, and any remaining blockers.
