begin;

-- Reconcile repo truth toward the staging-approved canonical baseline for decided objects only.
-- This migration is intentionally non-destructive: it adds/backfills canonical columns without removing
-- unresolved or legacy columns that still require separate proof and follow-up decisions.

alter table public.assets
  add column if not exists display_name text;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'assets'
      and column_name = 'name'
  ) then
    execute $sql$
      update public.assets
      set display_name = coalesce(display_name, name)
      where coalesce(display_name, '') = ''
        and name is not null
    $sql$;
  end if;
end
$$;

alter table public.asset_data_raw
  add column if not exists payload_jsonb jsonb;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'payload'
  ) then
    execute $sql$
      update public.asset_data_raw
      set payload_jsonb = payload
      where payload_jsonb is null
        and payload is not null
    $sql$;
  end if;
end
$$;

alter table public.asset_data_raw
  alter column payload_jsonb set default '{}'::jsonb;

update public.asset_data_raw
set payload_jsonb = '{}'::jsonb
where payload_jsonb is null;

alter table public.asset_data_raw
  alter column payload_jsonb set not null;

alter table public.asset_data_raw
  add column if not exists fetched_at timestamptz;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'created_at'
  ) then
    execute $sql$
      update public.asset_data_raw
      set fetched_at = coalesce(fetched_at, created_at, now())
      where fetched_at is null
    $sql$;
  else
    update public.asset_data_raw
    set fetched_at = now()
    where fetched_at is null;
  end if;
end
$$;

alter table public.asset_data_raw
  alter column fetched_at set default now();

alter table public.asset_data_raw
  alter column fetched_at set not null;

commit;
