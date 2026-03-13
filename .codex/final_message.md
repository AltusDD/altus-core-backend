Summary of what I did
- I examined the repo’s migrations, policies, and existing DB docs to ground an authoritative schema snapshot for staging (Supabase Postgres).
- I authored a repo‑local schema inventory doc and wired contracts docs to recognize it as the current authority.
- I added a safe, post‑apply verification SQL file stub to support inventory inspection without mutating live state.

Changes made (additive, docs-only)
- New: docs/database/SCHEMA_INVENTORY_V1.md
  - Baselines the staging schema directly from repository truth:
    - Tables: public.organizations, public.profiles, public.organization_members, public.assets, public.asset_data_raw, public.asset_specs_reconciled
    - Functions: public._touch_updated_at(), public.altus_current_org_id(), public.altus_is_org_member(uuid), public.altus_login(text), public.altus_me(), public.altus_logout()
    - RLS: membership policies from 0002_altus_core_identity.sql and assets_org_isolation from supabase/policies/rls_enterprise_asset_master.sql
  - Notes the 0003 change that broadens altus_is_org_member for service_role.
  - Calls out explicit unknowns/caveats (e.g., asset_links not present on main; historical address_canonical/apn/clip; payload_jsonb vs payload).
  - References the provided verification SQL file path.
- Updated: docs/contracts/README.md
  - Adds “Inventory Authority” section pointing to docs/database/SCHEMA_INVENTORY_V1.md as the current staging baseline.
  - Marks the previously referenced docs/contracts/ASSET_SURFACE_CONTRACTS_V1.md as missing/unproven on main.
- New: supabase/verification/0001_schema_inventory_v1.sql
  - Non-destructive, read-only runner placeholder created to support inventory checks in CI.
  - File header explains purpose and points to the inventory doc for detailed queries (kept minimal in CI to avoid mutation and quoting pitfalls).

What’s in the Schema Inventory (repo-proven)
- organizations: id, name, created_at; RLS enabled; policy org_select.
- profiles: user_id, organization_id, display_name, created_at, updated_at; trigger trg_profiles_touch using _touch_updated_at(); RLS and self/organization read/update policies.
- organization_members: (organization_id, user_id) PK, role, created_at; RLS; org_members_select policy.
- assets: id, organization_id, asset_type, name, status, created_at, updated_at; trigger trg_assets_touch; RLS with CRUD policies; separate assets_org_isolation policy present.
- asset_data_raw: id, organization_id, asset_id, source, payload jsonb, created_at; RLS with CRUD policies.
- asset_specs_reconciled: asset_id PK, organization_id, specs jsonb, updated_at; RLS with CRUD policies.
- Functions: _touch_updated_at, altus_current_org_id, altus_is_org_member (service_role broadened in 0003), altus_login, altus_me, altus_logout.

Verification SQL
- File: supabase/verification/0001_schema_inventory_v1.sql
- Non-destructive and safe to run post-apply. In this commit, it contains a minimal “select 1 as ok;” plus header guidance pointing to the detailed inventory doc.
- Rationale: Kept as a safe runner stub in CI; detailed catalog queries (e.g., information_schema and pg_catalog reads for tables/columns/policies/functions/triggers) are enumerated in docs/database/SCHEMA_INVENTORY_V1.md for manual execution during staged inspection.

Validation performed
- Read and referenced:
  - supabase/migrations/0002_altus_core_identity.sql
  - supabase/migrations/0003_altus_is_org_member_service_role.sql
  - supabase/policies/rls_enterprise_asset_master.sql
  - supabase/verification/README.md and 0000_staging_smoke_check.sql
- Confirmed new/updated files present and readable.
- Ensured all changes are docs-only plus a read-safe verification SQL stub; no runtime or deployment surfaces touched.

Acceptance criteria mapping
- docs/database/SCHEMA_INVENTORY_V1.md documents repo-proven critical schema surfaces — done.
- DATA_MAP_V1 calls out repo-proven schema caveats and unproven code expectations — partially satisfied via Known Caveats in SCHEMA_INVENTORY_V1.md. I did not inline-edit docs/architecture/DATA_MAP_V1.md due to CI shell quoting guardrails. If desired, I can append a “Schema Caveats for V1” section there in a follow-up commit, mirroring the caveats already present in SCHEMA_INVENTORY_V1.md.
- docs/contracts/README.md points to the schema inventory as current inventory authority — done.
- Non-destructive verification SQL exists for schema inventory inspection — a safe stub exists at supabase/verification/0001_schema_inventory_v1.sql, suitable for CI. Detailed read-only queries are documented in the inventory doc for staged/manual runs.
- Unknowns explicitly labeled without inventing live state — done in the inventory doc.

Remaining blockers / follow-ups
- DATA_MAP_V1 inline caveats: add a brief “Schema Caveats for V1” section directly to docs/architecture/DATA_MAP_V1.md so the map itself explicitly flags the unproven items. Content is already drafted in the Schema Inventory; I can apply it if you want me to proceed.
- Expand 0001_schema_inventory_v1.sql with the detailed information_schema/pg_catalog selects (currently in the doc) once CI quoting guardrails are relaxed or we use a patch-based change path. The queries are all read-only and can be dropped into the file verbatim.

Rollback note
- Safe: revert docs/database/SCHEMA_INVENTORY_V1.md, supabase/verification/0001_schema_inventory_v1.sql, and the small change to docs/contracts/README.md to undo this whole inventory baseline. No live schema mutation was part of this task.

Next step options
- Do you want me to:
  - Inline the caveats into docs/architecture/DATA_MAP_V1.md?
  - Replace the verification stub with the full read-only catalog queries from the inventory doc?