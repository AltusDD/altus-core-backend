-- Non-destructive staging discovery proof for public.assets.external_ids.

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
  and c.table_name = 'assets'
  and c.column_name = 'external_ids';

select
  to_regclass('public.assets') is not null as assets_exists,
  exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'assets'
      and column_name = 'external_ids'
  ) as external_ids_exists,
  pc.relrowsecurity as rls_enabled
from (select 1) seed
left join pg_class pc
  on pc.oid = to_regclass('public.assets');

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
  and rel.relname = 'assets'
  and att.attname = 'external_ids'
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
  and t.relname = 'assets'
  and att.attname = 'external_ids'
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
  and tablename = 'assets'
order by policyname;

drop table if exists pg_temp._external_ids_population;
drop table if exists pg_temp._external_ids_jsonb_shape;
drop table if exists pg_temp._external_ids_jsonb_keys;
drop table if exists pg_temp._external_ids_text_shape;

do $$
declare
  v_udt_name text;
begin
  select c.udt_name
  into v_udt_name
  from information_schema.columns c
  where c.table_schema = 'public'
    and c.table_name = 'assets'
    and c.column_name = 'external_ids';

  if v_udt_name is null then
    create temp table _external_ids_population (
      total_rows bigint,
      populated_rows bigint,
      empty_rows bigint,
      populated_ratio numeric(10,4)
    );
    insert into _external_ids_population values (null, null, null, null);

    create temp table _external_ids_jsonb_shape (
      top_level_kind text,
      row_count bigint
    );

    create temp table _external_ids_jsonb_keys (
      key_name text,
      row_count bigint
    );

    create temp table _external_ids_text_shape (
      shape_class text,
      row_count bigint
    );
  elsif v_udt_name in ('json', 'jsonb') then
    execute $sql$
      create temp table _external_ids_population as
      select
        count(*)::bigint as total_rows,
        count(external_ids)::bigint as populated_rows,
        (count(*) - count(external_ids))::bigint as empty_rows,
        round((count(external_ids)::numeric / nullif(count(*)::numeric, 0)), 4) as populated_ratio
      from public.assets
    $sql$;

    execute $sql$
      create temp table _external_ids_jsonb_shape as
      select
        jsonb_typeof(external_ids::jsonb) as top_level_kind,
        count(*)::bigint as row_count
      from public.assets
      where external_ids is not null
      group by jsonb_typeof(external_ids::jsonb)
      order by row_count desc, top_level_kind
    $sql$;

    execute $sql$
      create temp table _external_ids_jsonb_keys as
      select
        key_name,
        count(*)::bigint as row_count
      from (
        select distinct a.id, k.key_name
        from public.assets a
        cross join lateral jsonb_object_keys(
          case
            when jsonb_typeof(a.external_ids::jsonb) = 'object' then a.external_ids::jsonb
            else '{}'::jsonb
          end
        ) as k(key_name)
        where a.external_ids is not null
      ) dedup
      group by key_name
      order by row_count desc, key_name
    $sql$;

    create temp table _external_ids_text_shape (
      shape_class text,
      row_count bigint
    );
  else
    execute $sql$
      create temp table _external_ids_population as
      select
        count(*)::bigint as total_rows,
        count(external_ids)::bigint as populated_rows,
        (count(*) - count(external_ids))::bigint as empty_rows,
        round((count(external_ids)::numeric / nullif(count(*)::numeric, 0)), 4) as populated_ratio
      from public.assets
    $sql$;

    create temp table _external_ids_jsonb_shape (
      top_level_kind text,
      row_count bigint
    );

    create temp table _external_ids_jsonb_keys (
      key_name text,
      row_count bigint
    );

    execute $sql$
      create temp table _external_ids_text_shape as
      select
        case
          when btrim(external_ids::text) = '' then 'blank_text'
          when external_ids::text ~ '^\s*\{.*\}\s*$' then 'object_like_text'
          when external_ids::text ~ '^\s*\[.*\]\s*$' then 'array_like_text'
          when external_ids::text ~ '^[0-9a-fA-F-]{36}$' then 'uuid_like_text'
          else 'scalar_text'
        end as shape_class,
        count(*)::bigint as row_count
      from public.assets
      where external_ids is not null
      group by 1
      order by row_count desc, shape_class
    $sql$;
  end if;
end
$$;

select *
from pg_temp._external_ids_population;

select *
from pg_temp._external_ids_jsonb_shape;

select *
from pg_temp._external_ids_jsonb_keys;

select *
from pg_temp._external_ids_text_shape;
