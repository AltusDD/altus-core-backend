-- Non-destructive staging discovery proof for public.asset_data_raw.payload_sha256.

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
  and c.table_name = 'asset_data_raw'
  and c.column_name = 'payload_sha256';

select
  table_schema,
  table_name,
  column_name,
  data_type,
  udt_name,
  is_nullable,
  column_default
from information_schema.columns
where table_schema = 'public'
  and (
    (table_name = 'asset_data_raw' and column_name like '%hash%')
    or (table_name = 'assets' and column_name = 'external_ids')
  )
order by table_name, ordinal_position;

select
  to_regclass('public.asset_data_raw') is not null as asset_data_raw_exists,
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'payload_sha256'
  ) as payload_sha256_exists,
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'payload_jsonb'
  ) as payload_jsonb_exists,
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'assets'
      and column_name = 'external_ids'
  ) as external_ids_exists;

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
join unnest(con.conkey) with ordinality as ck(attnum, ord) on true
join pg_attribute att
  on att.attrelid = rel.oid
 and att.attnum = ck.attnum
where nsp.nspname = 'public'
  and rel.relname = 'asset_data_raw'
  and att.attname = 'payload_sha256'
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
join unnest(idx.indkey) with ordinality as ik(attnum, ord) on true
join pg_attribute att
  on att.attrelid = t.oid
 and att.attnum = ik.attnum
where n.nspname = 'public'
  and t.relname = 'asset_data_raw'
  and att.attname = 'payload_sha256'
order by indexname;

drop table if exists pg_temp._payload_sha256_population;
drop table if exists pg_temp._payload_jsonb_hash_keys;
drop table if exists pg_temp._external_ids_payload_hash;
drop table if exists pg_temp._provisional_conclusion;

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'payload_sha256'
  ) then
    execute $sql$
      create temp table _payload_sha256_population as
      select
        count(*)::bigint as total_rows,
        count(payload_sha256)::bigint as populated_rows,
        (count(*) - count(payload_sha256))::bigint as empty_rows,
        round((count(payload_sha256)::numeric / nullif(count(*)::numeric, 0)), 4) as populated_ratio,
        min(length(payload_sha256::text)) filter (where payload_sha256 is not null) as min_length,
        max(length(payload_sha256::text)) filter (where payload_sha256 is not null) as max_length
      from public.asset_data_raw
    $sql$;
  else
    create temp table _payload_sha256_population (
      total_rows bigint,
      populated_rows bigint,
      empty_rows bigint,
      populated_ratio numeric(10,4),
      min_length integer,
      max_length integer
    );
    insert into _payload_sha256_population values (null, null, null, null, null, null);
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'asset_data_raw'
      and column_name = 'payload_jsonb'
  ) then
    execute $sql$
      create temp table _payload_jsonb_hash_keys as
      select
        key_name,
        count(*)::bigint as row_count
      from (
        select distinct r.id, k.key_name
        from public.asset_data_raw r
        cross join lateral jsonb_object_keys(
          case
            when jsonb_typeof(r.payload_jsonb) = 'object' then r.payload_jsonb
            else '{}'::jsonb
          end
        ) as k(key_name)
        where r.payload_jsonb is not null
          and k.key_name in ('payload_hash', 'payload_sha256', 'sha256', 'hash')
      ) dedup
      group by key_name
      order by row_count desc, key_name
    $sql$;
  else
    create temp table _payload_jsonb_hash_keys (
      key_name text,
      row_count bigint
    );
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'assets'
      and column_name = 'external_ids'
  ) then
    execute $sql$
      create temp table _external_ids_payload_hash as
      select
        count(*)::bigint as total_asset_rows,
        count(*) filter (where external_ids ? 'payload_hash')::bigint as payload_hash_rows,
        count(*) filter (where external_ids = '{}'::jsonb)::bigint as empty_object_rows,
        round((count(*) filter (where external_ids ? 'payload_hash')::numeric / nullif(count(*)::numeric, 0)), 4) as payload_hash_ratio
      from public.assets
    $sql$;
  else
    create temp table _external_ids_payload_hash (
      total_asset_rows bigint,
      payload_hash_rows bigint,
      empty_object_rows bigint,
      payload_hash_ratio numeric(10,4)
    );
    insert into _external_ids_payload_hash values (null, null, null, null);
  end if;

  create temp table _provisional_conclusion as
  with flags as (
    select
      exists (
        select 1
        from information_schema.columns
        where table_schema = 'public'
          and table_name = 'asset_data_raw'
          and column_name = 'payload_sha256'
      ) as payload_sha256_exists,
      exists (select 1 from pg_temp._payload_jsonb_hash_keys where row_count > 0) as payload_jsonb_hash_exists,
      coalesce((select payload_hash_rows > 0 from pg_temp._external_ids_payload_hash), false) as external_ids_hash_exists
  )
  select
    payload_sha256_exists,
    payload_jsonb_hash_exists,
    external_ids_hash_exists,
    case
      when payload_sha256_exists then 'payload_sha256 exists in staging; runtime expectation is not drift for the live schema inspected here'
      when payload_jsonb_hash_exists or external_ids_hash_exists then 'equivalent representation elsewhere'
      else 'runtime-only expectation unsupported by staging truth'
    end as provisional_conclusion
  from flags;
end
$$;

select *
from pg_temp._payload_sha256_population;

select *
from pg_temp._payload_jsonb_hash_keys;

select *
from pg_temp._external_ids_payload_hash;

select *
from pg_temp._provisional_conclusion;
