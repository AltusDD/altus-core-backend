-- Proof-only discovery for normalized occupancy authority over the resolved public.assets portfolio cohort.

with relation_kinds as (
  select 'BASE TABLE'::text as relation_type, c.table_schema, c.table_name
  from information_schema.tables c
  where c.table_type = 'BASE TABLE'
    and c.table_schema not in ('pg_catalog', 'information_schema')
  union all
  select 'VIEW'::text as relation_type, v.table_schema, v.table_name
  from information_schema.views v
  where v.table_schema not in ('pg_catalog', 'information_schema')
),
matviews as (
  select 'MATERIALIZED VIEW'::text as relation_type, n.nspname as table_schema, c.relname as table_name
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where c.relkind = 'm'
    and n.nspname not in ('pg_catalog', 'information_schema')
),
all_relations as (
  select * from relation_kinds
  union all
  select * from matviews
),
columns as (
  select
    r.relation_type,
    c.table_schema,
    c.table_name,
    c.column_name,
    c.data_type,
    c.udt_name,
    c.is_nullable,
    c.column_default
  from information_schema.columns c
  join all_relations r
    on r.table_schema = c.table_schema
   and r.table_name = c.table_name
)
select
  relation_type,
  table_schema,
  table_name,
  column_name,
  data_type,
  udt_name,
  is_nullable,
  column_default
from columns
where column_name ~* '(occup|vacan|lease|tenant|resident)'
order by relation_type, table_schema, table_name, column_name;

with view_defs as (
  select
    'VIEW'::text as relation_type,
    schemaname as table_schema,
    viewname as table_name,
    definition
  from pg_views
  where schemaname not in ('pg_catalog', 'information_schema')
  union all
  select
    'MATERIALIZED VIEW'::text as relation_type,
    schemaname as table_schema,
    matviewname as table_name,
    definition
  from pg_matviews
  where schemaname not in ('pg_catalog', 'information_schema')
)
select
  relation_type,
  table_schema,
  table_name,
  case
    when definition ~* 'occup' then 'occupancy-term'
    when definition ~* 'vacan' then 'vacancy-term'
    when definition ~* 'lease|tenant|resident' then 'lease-or-tenant-term'
    else 'other'
  end as semantic_signal
from view_defs
where definition ~* '(occup|vacan|lease|tenant|resident)'
order by relation_type, table_schema, table_name;

select
  n.nspname as routine_schema,
  p.proname as routine_name,
  pg_get_function_identity_arguments(p.oid) as routine_arguments,
  case
    when p.proname ~* '(occup|vacan)' then 'occupancy-term'
    when p.proname ~* '(lease|tenant|resident)' then 'lease-or-tenant-term'
    else 'other'
  end as semantic_signal
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname not in ('pg_catalog', 'information_schema')
  and p.prokind = 'f'
  and p.proname ~* '(occup|vacan|lease|tenant|resident)'
order by routine_schema, routine_name, routine_arguments;

select
  c.table_schema,
  c.table_name,
  c.column_name,
  c.data_type,
  c.udt_name,
  c.is_nullable,
  c.column_default
from information_schema.columns c
where c.table_schema = 'public'
  and (
    (c.table_name = 'assets' and c.column_name in ('id', 'external_ids', 'status'))
    or (c.table_name = 'asset_specs_reconciled' and c.column_name in ('asset_id', 'organization_id', 'units_count', 'spec_version', 'provenance', 'effective_at', 'created_at'))
  )
order by c.table_name, c.ordinal_position;

select
  'public.assets'::text as source_name,
  'public.assets.external_ids[<configured_key>] == portfolioId'::text as join_path,
  'cohort membership only; no occupied-vs-vacant unit semantics are defined'::text as semantic_definition,
  null::text as completeness_or_nullability_risk
union all
select
  'public.asset_specs_reconciled',
  'join public.asset_specs_reconciled.asset_id to resolved public.assets.id cohort',
  'units_count supports totalUnits only; no occupied/vacant unit field is structurally present',
  'units_count is nullable and staging row count is currently 0'
union all
select
  'public.assets.status',
  'same resolved public.assets cohort, directly on public.assets.id',
  'asset lifecycle/state semantics only; no repo- or staging-proven mapping to occupied units',
  'status meaning does not prove unit occupancy semantics';

select
  (select count(*) from public.assets) as assets_row_count,
  (select count(*) from public.asset_specs_reconciled) as asset_specs_reconciled_row_count,
  (select count(*) from public.asset_specs_reconciled where units_count is not null) as asset_specs_units_count_nonnull_rows;

with occupancy_candidate_columns as (
  select count(*)::bigint as count_candidates
  from information_schema.columns c
  where c.table_schema not in ('pg_catalog', 'information_schema')
    and c.column_name ~* '(occup|vacan|lease|tenant|resident)'
),
occupancy_candidate_views as (
  select count(*)::bigint as count_candidates
  from (
    select schemaname, viewname as relname, definition
    from pg_views
    where schemaname not in ('pg_catalog', 'information_schema')
    union all
    select schemaname, matviewname as relname, definition
    from pg_matviews
    where schemaname not in ('pg_catalog', 'information_schema')
  ) q
  where definition ~* '(occup|vacan|lease|tenant|resident)'
),
occupancy_candidate_routines as (
  select count(*)::bigint as count_candidates
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname not in ('pg_catalog', 'information_schema')
    and p.prokind = 'f'
    and p.proname ~* '(occup|vacan|lease|tenant|resident)'
)
select
  occ_cols.count_candidates as occupancy_like_columns,
  occ_views.count_candidates as occupancy_like_views,
  occ_routines.count_candidates as occupancy_like_routines,
  case
    when occ_cols.count_candidates = 0 and occ_views.count_candidates = 0 and occ_routines.count_candidates = 0
      then 'not provable'
    else 'provable candidate requires manual review'
  end as final_decision,
  case
    when occ_cols.count_candidates = 0 and occ_views.count_candidates = 0 and occ_routines.count_candidates = 0
      then 'No normalized or analytical occupancy authority is structurally discoverable for the resolved public.assets cohort in current staging.'
    else 'At least one occupancy-like structure was discovered and requires semantic review before activation.'
  end as decision_reason
from occupancy_candidate_columns occ_cols
cross join occupancy_candidate_views occ_views
cross join occupancy_candidate_routines occ_routines;



