# SCHEMA_INVENTORY_V1

Target environment: staging (Supabase Postgres)
Target project/ref: SUPABASE_STAGING_PROJECT_REF
Baseline source of truth: repository artifacts on main @ commit bafc2e1

Scope: repo-proven critical schema surfaces used by Altus backend services. This document inventories only what is defined in this repository (migrations and policies). Anything not present here is treated as unproven until verified in a later staged inspection.

## Inventory Derivation
- Tables, functions, triggers, and RLS policies come from:
  - supabase/migrations/0002_altus_core_identity.sql
  - supabase/migrations/0003_altus_is_org_member_service_role.sql (broadens service role check)
  - supabase/policies/rls_enterprise_asset_master.sql (adds assets_org_isolation)
- Historical file supabase/migrations/0001_enterprise_asset_master.sql exists but is superseded by 0002 in this repo baseline.

## Tables (public schema)

### organizations
- Columns: id uuid pk default gen_random_uuid(), name text not null, created_at timestamptz not null default now()
- RLS: enabled
- Policies: org_select (select using public.altus_is_org_member(id)).

### profiles
- Columns: user_id uuid pk references auth.users on delete cascade, organization_id uuid references public.organizations on delete set null, display_name text, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
- Triggers: trg_profiles_touch (before update -> public._touch_updated_at())
- RLS: enabled
- Policies: profiles_select_self (read own or org members), profiles_update_self (update self).

### organization_members
- Columns: organization_id uuid not null references public.organizations on delete cascade, user_id uuid not null references auth.users on delete cascade, role text not null default 'owner', created_at timestamptz not null default now(), primary key (organization_id, user_id)
- RLS: enabled
- Policies: org_members_select (org members can read membership rows for their org).

### assets
- Columns: id uuid pk default gen_random_uuid(), organization_id uuid not null references public.organizations on delete cascade, asset_type text not null default 'unknown', name text, status text not null default 'active', created_at timestamptz not null default now(), updated_at timestamptz not null default now()
- Triggers: trg_assets_touch (before update -> public._touch_updated_at())
- RLS: enabled
- Policies (repo-defined): assets_select, assets_insert, assets_update, assets_delete (all enforce membership via public.altus_is_org_member(organization_id)).
- Policies (separate file): assets_org_isolation from supabase/policies/rls_enterprise_asset_master.sql uses the JWT claim request.jwt.claim.organization_id for all commands.

### asset_data_raw
- Columns: id uuid pk default gen_random_uuid(), organization_id uuid not null references public.organizations on delete cascade, asset_id uuid not null references public.assets on delete cascade, source text not null, payload jsonb not null default '{}'::jsonb, created_at timestamptz not null default now()
- RLS: enabled
- Policies: adr_select, adr_insert, adr_update, adr_delete (each checks membership through the owning asset's org).

### asset_specs_reconciled
- Columns: asset_id uuid pk references public.assets on delete cascade, organization_id uuid not null references public.organizations on delete cascade, specs jsonb not null default '{}'::jsonb, updated_at timestamptz not null default now()
- RLS: enabled
- Policies: asr_select, asr_insert, asr_update, asr_delete (membership on organization_id).

## Functions
- public._touch_updated_at() — plpgsql trigger function that sets updated_at = now() on update.
- public.altus_current_org_id() — stable SQL function; returns the caller's profiles.organization_id by auth.uid().
- public.altus_is_org_member(org_id uuid) — stable SQL function used by RLS. Modified in 0003 to return true for auth.role() = 'service_role' callers; otherwise checks membership.
- public.altus_login(org_name text default 'Altus Realty Group') — security definer; ensures profile/org/membership for the caller and returns public.altus_me().
- public.altus_me() — security definer; returns a jsonb envelope with user, organization, and role for auth.uid().
- public.altus_logout() — security definer; simple jsonb { ok: true }.

## RLS Policies (named)
- organizations: org_select
- profiles: profiles_select_self, profiles_update_self
- organization_members: org_members_select
- assets: assets_select, assets_insert, assets_update, assets_delete, and assets_org_isolation
- asset_data_raw: adr_select, adr_insert, adr_update, adr_delete
- asset_specs_reconciled: asr_select, asr_insert, asr_update, asr_delete

## Known Caveats and Unknowns
- asset_links is referenced by runtime notes elsewhere but is NOT present in repository migrations; treated as unproven for staging until verified.
- Historical columns such as assets.address_canonical, assets.apn, assets.clip, and asset_data_raw.payload_jsonb exist only in 0001_enterprise_asset_master.sql and are not present in the 0002 baseline; treated as historical/unproven for staging.
- Two policy layers exist for public.assets (membership policies and assets_org_isolation). In Postgres, multiple permissive policies of the same command combine with OR semantics; effective enforcement should be validated in staging to ensure intent alignment before tightening.
- Any dashboard-only edits are non-authoritative until backfilled into repository artifacts.

## Verification
A read-only verification script is provided at supabase/verification/0001_schema_inventory_v1.sql to inspect the presence of tables, columns, functions, triggers, and policies listed above in the target staging project. It is safe to run post-apply and produces rowsets only.
