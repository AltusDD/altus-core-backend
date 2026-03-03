-- ALTUS CORE: Identity + Org Scoping + Asset Master (Foundation)
-- Creates:
--   organizations, profiles, organization_members
--   assets, asset_data_raw, asset_specs_reconciled
-- Adds:
--   RLS org enforcement everywhere
--   RPCs: altus_login, altus_me, altus_logout
-- Notes:
--   - Uses auth.uid() (Supabase Auth)
--   - Does NOT use service_role in clients
--   - All access is scoped to the caller's organization membership

begin;

-- Extensions
create extension if not exists "pgcrypto";

-- -------------------------
-- Tables: Core Identity
-- -------------------------

create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  organization_id uuid references public.organizations(id) on delete set null,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.organization_members (
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'owner',
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

-- -------------------------
-- Tables: Enterprise Asset Master (minimal)
-- -------------------------

create table if not exists public.assets (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  asset_type text not null default 'unknown',
  name text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.asset_data_raw (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  asset_id uuid not null references public.assets(id) on delete cascade,
  source text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.asset_specs_reconciled (
  asset_id uuid primary key references public.assets(id) on delete cascade,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  specs jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

-- -------------------------
-- Timestamps
-- -------------------------

create or replace function public._touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_profiles_touch on public.profiles;
create trigger trg_profiles_touch
before update on public.profiles
for each row execute function public._touch_updated_at();

drop trigger if exists trg_assets_touch on public.assets;
create trigger trg_assets_touch
before update on public.assets
for each row execute function public._touch_updated_at();

-- -------------------------
-- Helper functions (RLS)
-- -------------------------

create or replace function public.altus_current_org_id()
returns uuid
language sql
stable
as $$
  select p.organization_id
  from public.profiles p
  where p.user_id = auth.uid();
$$;

create or replace function public.altus_is_org_member(org_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from public.organization_members m
    where m.organization_id = org_id
      and m.user_id = auth.uid()
  );
$$;

-- -------------------------
-- RLS Enablement
-- -------------------------

alter table public.organizations enable row level security;
alter table public.profiles enable row level security;
alter table public.organization_members enable row level security;
alter table public.assets enable row level security;
alter table public.asset_data_raw enable row level security;
alter table public.asset_specs_reconciled enable row level security;

-- -------------------------
-- RLS Policies
-- -------------------------

-- organizations: member can read their org
drop policy if exists org_select on public.organizations;
create policy org_select
on public.organizations
for select
using (public.altus_is_org_member(id));

-- profiles: user can read/update their own; org members can read (optional)
drop policy if exists profiles_select_self on public.profiles;
create policy profiles_select_self
on public.profiles
for select
using (
  user_id = auth.uid()
  or public.altus_is_org_member(organization_id)
);

drop policy if exists profiles_update_self on public.profiles;
create policy profiles_update_self
on public.profiles
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

-- org members: member can read org membership rows for their org
drop policy if exists org_members_select on public.organization_members;
create policy org_members_select
on public.organization_members
for select
using (public.altus_is_org_member(organization_id));

-- assets: org members can CRUD within org
drop policy if exists assets_select on public.assets;
create policy assets_select
on public.assets
for select
using (public.altus_is_org_member(organization_id));

drop policy if exists assets_insert on public.assets;
create policy assets_insert
on public.assets
for insert
with check (public.altus_is_org_member(organization_id));

drop policy if exists assets_update on public.assets;
create policy assets_update
on public.assets
for update
using (public.altus_is_org_member(organization_id))
with check (public.altus_is_org_member(organization_id));

drop policy if exists assets_delete on public.assets;
create policy assets_delete
on public.assets
for delete
using (public.altus_is_org_member(organization_id));

-- asset_data_raw: org members can CRUD within org
drop policy if exists adr_select on public.asset_data_raw;
create policy adr_select
on public.asset_data_raw
for select
using (
  exists (
    select 1
    from public.assets a
    where a.id = asset_data_raw.asset_id
      and public.altus_is_org_member(a.organization_id)
  )
);

drop policy if exists adr_insert on public.asset_data_raw;
create policy adr_insert
on public.asset_data_raw
for insert
with check (
  exists (
    select 1
    from public.assets a
    where a.id = asset_data_raw.asset_id
      and public.altus_is_org_member(a.organization_id)
  )
);

drop policy if exists adr_update on public.asset_data_raw;
create policy adr_update
on public.asset_data_raw
for update
using (
  exists (
    select 1
    from public.assets a
    where a.id = asset_data_raw.asset_id
      and public.altus_is_org_member(a.organization_id)
  )
)
with check (
  exists (
    select 1
    from public.assets a
    where a.id = asset_data_raw.asset_id
      and public.altus_is_org_member(a.organization_id)
  )
);

drop policy if exists adr_delete on public.asset_data_raw;
create policy adr_delete
on public.asset_data_raw
for delete
using (
  exists (
    select 1
    from public.assets a
    where a.id = asset_data_raw.asset_id
      and public.altus_is_org_member(a.organization_id)
  )
);

-- asset_specs_reconciled: org members can read/update within org
drop policy if exists asr_select on public.asset_specs_reconciled;
create policy asr_select
on public.asset_specs_reconciled
for select
using (public.altus_is_org_member(organization_id));

drop policy if exists asr_insert on public.asset_specs_reconciled;
create policy asr_insert
on public.asset_specs_reconciled
for insert
with check (public.altus_is_org_member(organization_id));

drop policy if exists asr_update on public.asset_specs_reconciled;
create policy asr_update
on public.asset_specs_reconciled
for update
using (public.altus_is_org_member(organization_id))
with check (public.altus_is_org_member(organization_id));

drop policy if exists asr_delete on public.asset_specs_reconciled;
create policy asr_delete
on public.asset_specs_reconciled
for delete
using (public.altus_is_org_member(organization_id));

-- -------------------------
-- RPCs
-- -------------------------

-- altus_login: ensure caller has org + membership + profile; return "me"
create or replace function public.altus_login(org_name text default 'Altus Realty Group')
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid uuid := auth.uid();
  v_org_id uuid;
begin
  if v_uid is null then
    raise exception 'Not authenticated';
  end if;

  -- 1) Ensure profile exists
  insert into public.profiles (user_id, display_name)
  values (v_uid, null)
  on conflict (user_id) do nothing;

  -- 2) If profile has no org, create one and attach
  select organization_id into v_org_id
  from public.profiles
  where user_id = v_uid;

  if v_org_id is null then
    insert into public.organizations (name)
    values (coalesce(nullif(org_name,''), 'Altus Realty Group'))
    returning id into v_org_id;

    update public.profiles
    set organization_id = v_org_id
    where user_id = v_uid;
  end if;

  -- 3) Ensure membership exists
  insert into public.organization_members (organization_id, user_id, role)
  values (v_org_id, v_uid, 'owner')
  on conflict (organization_id, user_id) do nothing;

  return public.altus_me();
end;
$$;

-- altus_me: returns org + profile + role
create or replace function public.altus_me()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with me as (
    select
      p.user_id,
      p.display_name,
      p.organization_id
    from public.profiles p
    where p.user_id = auth.uid()
  ),
  org as (
    select o.id, o.name, o.created_at
    from public.organizations o
    join me on me.organization_id = o.id
  ),
  role as (
    select m.role
    from public.organization_members m
    join me on me.organization_id = m.organization_id
    where m.user_id = auth.uid()
    limit 1
  )
  select jsonb_build_object(
    'user_id', (select user_id from me),
    'display_name', (select display_name from me),
    'organization', jsonb_build_object(
      'id', (select id from org),
      'name', (select name from org),
      'created_at', (select created_at from org)
    ),
    'role', coalesce((select role from role), 'member')
  );
$$;

-- altus_logout: no-op placeholder (clients can just delete their local token/cookie)
create or replace function public.altus_logout()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  select jsonb_build_object('ok', true);
$$;

-- Tighten function execution: only authenticated users
revoke all on function public.altus_login(text) from public;
revoke all on function public.altus_me() from public;
revoke all on function public.altus_logout() from public;

grant execute on function public.altus_login(text) to authenticated;
grant execute on function public.altus_me() to authenticated;
grant execute on function public.altus_logout() to authenticated;

commit;
