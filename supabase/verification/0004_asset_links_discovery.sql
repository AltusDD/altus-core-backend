-- Non-destructive staging discovery proof for public.asset_links.

select
  current_database() as database_name,
  current_schema() as current_schema,
  to_regclass('public.asset_links') is not null as asset_links_exists,
  c.relkind as relation_kind,
  c.relrowsecurity as rls_enabled
from (select 1) seed
left join pg_class c
  on c.oid = to_regclass('public.asset_links');

select
  ordinal_position,
  column_name,
  data_type,
  is_nullable,
  column_default
from information_schema.columns
where table_schema = 'public'
  and table_name = 'asset_links'
order by ordinal_position;

select
  con.conname as constraint_name,
  case con.contype
    when 'p' then 'primary_key'
    when 'f' then 'foreign_key'
    when 'u' then 'unique'
    when 'c' then 'check'
    else con.contype::text
  end as constraint_type,
  pg_get_constraintdef(con.oid) as constraint_definition
from pg_constraint con
where con.conrelid = to_regclass('public.asset_links')
order by constraint_type, constraint_name;

select
  schemaname,
  tablename,
  indexname,
  indexdef
from pg_indexes
where schemaname = 'public'
  and tablename = 'asset_links'
order by indexname;

select
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
from pg_policies
where schemaname = 'public'
  and tablename = 'asset_links'
order by policyname;

drop table if exists pg_temp._asset_links_row_count;

do $$
begin
  if to_regclass('public.asset_links') is not null then
    execute 'create temp table _asset_links_row_count as select count(*)::bigint as row_count from public.asset_links';
  else
    create temp table _asset_links_row_count (row_count bigint);
    insert into _asset_links_row_count (row_count) values (null);
  end if;
end
$$;

select row_count
from pg_temp._asset_links_row_count;

select
  count(*) filter (
    where source like 'ASSET_LINK::%'
       or source like 'ASSET_LINK_DELETE::%'
  ) as source_prefix_fallback_rows,
  count(*) filter (
    where coalesce(payload_jsonb ->> 'record_type', '') in ('asset_link', 'asset_link_delete')
  ) as payload_record_type_fallback_rows,
  count(*) filter (
    where source like 'ASSET_LINK::%'
       or source like 'ASSET_LINK_DELETE::%'
       or coalesce(payload_jsonb ->> 'record_type', '') in ('asset_link', 'asset_link_delete')
  ) as total_fallback_link_evidence_rows
from public.asset_data_raw;

select
  to_regclass('public.asset_links') is not null as asset_links_exists,
  case
    when to_regclass('public.asset_links') is null then 'asset_data_raw remains the only proven link authority for this staging proof run'
    else 'asset_links exists in staging; authority requires follow-up decision from this proof output'
  end as authority_statement;
