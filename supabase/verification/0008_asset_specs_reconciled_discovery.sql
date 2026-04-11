-- Non-destructive staging discovery proof for extra live columns on public.asset_specs_reconciled.

select
  c.table_schema,
  c.table_name,
  c.column_name,
  c.ordinal_position,
  c.data_type,
  c.udt_name,
  c.is_nullable,
  c.column_default
from information_schema.columns c
where c.table_schema = 'public'
  and c.table_name = 'asset_specs_reconciled'
order by c.ordinal_position;

with repo_proven(column_name) as (
  values
    ('asset_id'),
    ('organization_id'),
    ('beds'),
    ('baths'),
    ('sqft'),
    ('year_built'),
    ('property_type'),
    ('units_count'),
    ('updated_at'),
    ('updated_by_user_id'),
    ('specs')
)
select
  c.column_name,
  c.ordinal_position,
  c.data_type,
  c.udt_name,
  c.is_nullable,
  c.column_default
from information_schema.columns c
left join repo_proven rp
  on rp.column_name = c.column_name
where c.table_schema = 'public'
  and c.table_name = 'asset_specs_reconciled'
  and rp.column_name is null
order by c.ordinal_position;

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
join pg_class rel
  on rel.oid = con.conrelid
join pg_namespace nsp
  on nsp.oid = rel.relnamespace
where nsp.nspname = 'public'
  and rel.relname = 'asset_specs_reconciled'
order by constraint_type, constraint_name;

select
  n.nspname as schemaname,
  t.relname as tablename,
  i.relname as indexname,
  pg_get_indexdef(i.oid) as indexdef
from pg_index idx
join pg_class t
  on t.oid = idx.indrelid
join pg_namespace n
  on n.oid = t.relnamespace
join pg_class i
  on i.oid = idx.indexrelid
where n.nspname = 'public'
  and t.relname = 'asset_specs_reconciled'
order by indexname;

select
  c.relrowsecurity as rls_enabled,
  c.relforcerowsecurity as rls_forced
from pg_class c
join pg_namespace n
  on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relname = 'asset_specs_reconciled';

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
  and tablename = 'asset_specs_reconciled'
order by policyname;

drop table if exists pg_temp._asset_specs_extra_column_population;
drop table if exists pg_temp._asset_specs_shape_summary;
drop table if exists pg_temp._asset_specs_versioning_summary;
drop table if exists pg_temp._asset_specs_provenance_summary;
drop table if exists pg_temp._asset_specs_temporal_summary;
drop table if exists pg_temp._asset_specs_semantic_hints;

do $$
declare
  table_exists boolean;
  specs_udt text;
  provenance_udt text;
  has_asset_id boolean;
  has_id boolean;
  has_org boolean;
  has_spec_version boolean;
  has_provenance boolean;
  has_effective_at boolean;
  has_created_at boolean;
begin
  select to_regclass('public.asset_specs_reconciled') is not null into table_exists;

  create temp table _asset_specs_extra_column_population (
    column_name text,
    total_rows bigint,
    populated_rows bigint,
    empty_rows bigint,
    populated_ratio numeric(10,4),
    distinct_nonnull_values bigint,
    min_text_length integer,
    max_text_length integer,
    notes text
  );

  create temp table _asset_specs_shape_summary (
    total_rows bigint,
    distinct_asset_ids bigint,
    distinct_org_ids bigint,
    distinct_row_ids bigint,
    object_shaped_specs_rows bigint,
    notes text
  );

  create temp table _asset_specs_versioning_summary (
    assets_with_multiple_rows bigint,
    max_rows_per_asset bigint,
    distinct_spec_versions bigint,
    populated_spec_version_rows bigint,
    assets_with_multiple_spec_versions bigint,
    notes text
  );

  create temp table _asset_specs_provenance_summary (
    populated_provenance_rows bigint,
    distinct_provenance_values bigint,
    object_shaped_provenance_rows bigint,
    array_shaped_provenance_rows bigint,
    scalar_or_text_provenance_rows bigint,
    notes text
  );

  create temp table _asset_specs_temporal_summary (
    populated_effective_at_rows bigint,
    populated_created_at_rows bigint,
    min_effective_at text,
    max_effective_at text,
    min_created_at text,
    max_created_at text,
    assets_with_multiple_effective_at_values bigint,
    notes text
  );

  create temp table _asset_specs_semantic_hints (
    semantic_axis text,
    signal text,
    interpretation text
  );

  if not table_exists then
    insert into _asset_specs_extra_column_population values
      ('id', null, null, null, null, null, null, null, 'table absent'),
      ('organization_id', null, null, null, null, null, null, null, 'table absent'),
      ('spec_version', null, null, null, null, null, null, null, 'table absent'),
      ('provenance', null, null, null, null, null, null, null, 'table absent'),
      ('effective_at', null, null, null, null, null, null, null, 'table absent'),
      ('created_at', null, null, null, null, null, null, null, 'table absent');
    insert into _asset_specs_shape_summary values (null, null, null, null, null, 'table absent');
    insert into _asset_specs_versioning_summary values (null, null, null, null, null, 'table absent');
    insert into _asset_specs_provenance_summary values (null, null, null, null, null, 'table absent');
    insert into _asset_specs_temporal_summary values (null, null, null, null, null, null, null, 'table absent');
    insert into _asset_specs_semantic_hints values ('table_presence', 'absent', 'public.asset_specs_reconciled is not present in staging');
    return;
  end if;

  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'asset_id'
  ) into has_asset_id;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'id'
  ) into has_id;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'organization_id'
  ) into has_org;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'spec_version'
  ) into has_spec_version;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'provenance'
  ) into has_provenance;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'effective_at'
  ) into has_effective_at;
  select exists (
    select 1 from information_schema.columns
    where table_schema = 'public' and table_name = 'asset_specs_reconciled' and column_name = 'created_at'
  ) into has_created_at;

  select c.udt_name
  into specs_udt
  from information_schema.columns c
  where c.table_schema = 'public'
    and c.table_name = 'asset_specs_reconciled'
    and c.column_name = 'specs';

  select c.udt_name
  into provenance_udt
  from information_schema.columns c
  where c.table_schema = 'public'
    and c.table_name = 'asset_specs_reconciled'
    and c.column_name = 'provenance';

  if has_id then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'id',
        count(*)::bigint,
        count(id)::bigint,
        (count(*) - count(id))::bigint,
        round((count(id)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct id)::bigint,
        min(length(id::text)) filter (where id is not null),
        max(length(id::text)) filter (where id is not null),
        'row identifier population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('id', null, null, null, null, null, null, null, 'column absent');
  end if;

  if has_org then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'organization_id',
        count(*)::bigint,
        count(organization_id)::bigint,
        (count(*) - count(organization_id))::bigint,
        round((count(organization_id)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct organization_id)::bigint,
        min(length(organization_id::text)) filter (where organization_id is not null),
        max(length(organization_id::text)) filter (where organization_id is not null),
        'organization scoping population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('organization_id', null, null, null, null, null, null, null, 'column absent');
  end if;

  if has_spec_version then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'spec_version',
        count(*)::bigint,
        count(spec_version)::bigint,
        (count(*) - count(spec_version))::bigint,
        round((count(spec_version)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct spec_version)::bigint,
        min(length(spec_version::text)) filter (where spec_version is not null),
        max(length(spec_version::text)) filter (where spec_version is not null),
        'version discriminator population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('spec_version', null, null, null, null, null, null, null, 'column absent');
  end if;

  if has_provenance then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'provenance',
        count(*)::bigint,
        count(provenance)::bigint,
        (count(*) - count(provenance))::bigint,
        round((count(provenance)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct provenance::text)::bigint,
        min(length(provenance::text)) filter (where provenance is not null),
        max(length(provenance::text)) filter (where provenance is not null),
        'provenance payload population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('provenance', null, null, null, null, null, null, null, 'column absent');
  end if;

  if has_effective_at then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'effective_at',
        count(*)::bigint,
        count(effective_at)::bigint,
        (count(*) - count(effective_at))::bigint,
        round((count(effective_at)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct effective_at)::bigint,
        min(length(effective_at::text)) filter (where effective_at is not null),
        max(length(effective_at::text)) filter (where effective_at is not null),
        'effective dating population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('effective_at', null, null, null, null, null, null, null, 'column absent');
  end if;

  if has_created_at then
    execute $sql$
      insert into _asset_specs_extra_column_population
      select
        'created_at',
        count(*)::bigint,
        count(created_at)::bigint,
        (count(*) - count(created_at))::bigint,
        round((count(created_at)::numeric / nullif(count(*)::numeric, 0)), 4),
        count(distinct created_at)::bigint,
        min(length(created_at::text)) filter (where created_at is not null),
        max(length(created_at::text)) filter (where created_at is not null),
        'creation timestamp population'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_extra_column_population values ('created_at', null, null, null, null, null, null, null, 'column absent');
  end if;

  execute format($sql$
    insert into _asset_specs_shape_summary
    select
      count(*)::bigint,
      %s,
      %s,
      %s,
      %s,
      'table shape summary'
    from public.asset_specs_reconciled
  $sql$,
    case when has_asset_id then 'count(distinct asset_id)::bigint' else 'null::bigint' end,
    case when has_org then 'count(distinct organization_id)::bigint' else 'null::bigint' end,
    case when has_id then 'count(distinct id)::bigint' else 'null::bigint' end,
    case when specs_udt = 'jsonb' then 'count(*) filter (where jsonb_typeof(specs) = ''object'')::bigint' else 'null::bigint' end
  );

  if has_asset_id then
    execute format($sql$
      insert into _asset_specs_versioning_summary
      with per_asset as (
        select
          asset_id,
          count(*)::bigint as row_count,
          %s as distinct_spec_versions
        from public.asset_specs_reconciled
        group by asset_id
      )
      select
        count(*) filter (where row_count > 1)::bigint,
        max(row_count)::bigint,
        %s,
        %s,
        %s,
        'versioning and multi-row-per-asset hints'
      from per_asset
    $sql$,
      case when has_spec_version then 'count(distinct spec_version::text)::bigint' else 'null::bigint' end,
      case when has_spec_version then '(select count(distinct spec_version::text)::bigint from public.asset_specs_reconciled)' else 'null::bigint' end,
      case when has_spec_version then '(select count(spec_version)::bigint from public.asset_specs_reconciled)' else 'null::bigint' end,
      case when has_spec_version then 'count(*) filter (where distinct_spec_versions > 1)::bigint' else 'null::bigint' end
    );
  else
    insert into _asset_specs_versioning_summary values (null, null, null, null, null, 'asset_id absent; versioning summary unavailable');
  end if;

  if has_provenance and provenance_udt = 'jsonb' then
    execute $sql$
      insert into _asset_specs_provenance_summary
      select
        count(provenance)::bigint,
        count(distinct provenance::text)::bigint,
        count(*) filter (where provenance is not null and jsonb_typeof(provenance) = 'object')::bigint,
        count(*) filter (where provenance is not null and jsonb_typeof(provenance) = 'array')::bigint,
        count(*) filter (where provenance is not null and jsonb_typeof(provenance) not in ('object', 'array'))::bigint,
        'provenance jsonb shape summary'
      from public.asset_specs_reconciled
    $sql$;
  elsif has_provenance then
    execute $sql$
      insert into _asset_specs_provenance_summary
      select
        count(provenance)::bigint,
        count(distinct provenance::text)::bigint,
        null::bigint,
        null::bigint,
        count(provenance)::bigint,
        'provenance populated, but non-jsonb type limits shape inspection'
      from public.asset_specs_reconciled
    $sql$;
  else
    insert into _asset_specs_provenance_summary values (null, null, null, null, null, 'provenance absent');
  end if;

  execute format($sql$
    insert into _asset_specs_temporal_summary
    select
      %s,
      %s,
      %s,
      %s,
      %s,
      %s,
      %s,
      'temporal and effective-dating summary'
  $sql$,
    case when has_effective_at then '(select count(effective_at)::bigint from public.asset_specs_reconciled)' else 'null::bigint' end,
    case when has_created_at then '(select count(created_at)::bigint from public.asset_specs_reconciled)' else 'null::bigint' end,
    case when has_effective_at then '(select min(effective_at)::text from public.asset_specs_reconciled)' else 'null::text' end,
    case when has_effective_at then '(select max(effective_at)::text from public.asset_specs_reconciled)' else 'null::text' end,
    case when has_created_at then '(select min(created_at)::text from public.asset_specs_reconciled)' else 'null::text' end,
    case when has_created_at then '(select max(created_at)::text from public.asset_specs_reconciled)' else 'null::text' end,
    case when has_asset_id and has_effective_at then '(select count(*)::bigint from (select asset_id from public.asset_specs_reconciled group by asset_id having count(distinct effective_at) > 1) s)' else 'null::bigint' end
  );

  insert into _asset_specs_semantic_hints
  select
    'versioning',
    case
      when coalesce(assets_with_multiple_rows, 0) > 0 or coalesce(populated_spec_version_rows, 0) > 0 then 'present'
      else 'weak'
    end,
    case
      when coalesce(assets_with_multiple_spec_versions, 0) > 0 then 'rows suggest explicit version progression per asset'
      when coalesce(assets_with_multiple_rows, 0) > 0 and coalesce(populated_spec_version_rows, 0) = 0 then 'multiple rows per asset exist but explicit spec_version usage is not proven'
      when coalesce(populated_spec_version_rows, 0) > 0 then 'spec_version is populated, but multi-version-per-asset behavior is limited or absent in aggregate staging data'
      else 'no strong versioning signal proven from aggregate staging data'
    end
  from _asset_specs_versioning_summary;

  insert into _asset_specs_semantic_hints
  select
    'provenance',
    case
      when coalesce(populated_provenance_rows, 0) > 0 then 'present'
      else 'absent'
    end,
    case
      when coalesce(object_shaped_provenance_rows, 0) > 0 then 'rows suggest structured provenance tracking payloads'
      when coalesce(array_shaped_provenance_rows, 0) > 0 then 'rows suggest list-style provenance tracking payloads'
      when coalesce(populated_provenance_rows, 0) > 0 then 'rows suggest provenance tracking is present but shape inspection is limited'
      else 'no provenance tracking payload is proven populated from aggregate staging data'
    end
  from _asset_specs_provenance_summary;

  insert into _asset_specs_semantic_hints
  select
    'temporal',
    case
      when coalesce(populated_effective_at_rows, 0) > 0 or coalesce(populated_created_at_rows, 0) > 0 then 'present'
      else 'weak'
    end,
    case
      when coalesce(assets_with_multiple_effective_at_values, 0) > 0 then 'rows suggest effective-dating across multiple values per asset'
      when coalesce(populated_effective_at_rows, 0) > 0 and coalesce(populated_created_at_rows, 0) > 0 then 'rows suggest temporal tracking fields are active, but per-asset effective-date variation is limited or absent'
      when coalesce(populated_effective_at_rows, 0) > 0 then 'effective_at is populated and likely supports temporal semantics'
      when coalesce(populated_created_at_rows, 0) > 0 then 'created_at is populated and likely supports record creation tracking'
      else 'no strong temporal or effective-dating signal proven from aggregate staging data'
    end
  from _asset_specs_temporal_summary;
end
$$;

select *
from pg_temp._asset_specs_extra_column_population
order by column_name;

select *
from pg_temp._asset_specs_shape_summary;

select *
from pg_temp._asset_specs_versioning_summary;

select *
from pg_temp._asset_specs_provenance_summary;

select *
from pg_temp._asset_specs_temporal_summary;

select *
from pg_temp._asset_specs_semantic_hints
order by semantic_axis;
