-- Non-destructive verification for the approved canonical baseline decisions only.

select table_name, column_name, data_type, is_nullable
from information_schema.columns
where table_schema = 'public'
  and (
    (table_name = 'assets' and column_name in ('name', 'display_name'))
    or (table_name = 'asset_data_raw' and column_name in ('payload_jsonb', 'fetched_at', 'organization_id', 'payload', 'created_at'))
  )
order by table_name, ordinal_position;

select schemaname, tablename, policyname, permissive, roles, cmd
from pg_policies
where schemaname = 'public'
  and tablename = 'assets'
order by policyname;
