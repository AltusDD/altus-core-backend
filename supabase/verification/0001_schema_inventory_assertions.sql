-- Non-destructive schema inventory verification for critical DB autonomy surfaces.

select table_schema, table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'organizations',
    'profiles',
    'organization_members',
    'assets',
    'asset_data_raw',
    'asset_specs_reconciled'
  )
order by table_name;

select table_name, column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and table_name in (
    'organizations',
    'profiles',
    'organization_members',
    'assets',
    'asset_data_raw',
    'asset_specs_reconciled'
  )
order by table_name, ordinal_position;

select routine_schema, routine_name, routine_type
from information_schema.routines
where routine_schema = 'public'
  and routine_name in (
    '_touch_updated_at',
    'altus_current_org_id',
    'altus_is_org_member',
    'altus_login',
    'altus_me',
    'altus_logout'
  )
order by routine_name;

select schemaname, tablename, policyname, permissive, roles, cmd
from pg_policies
where schemaname = 'public'
  and tablename in (
    'organizations',
    'profiles',
    'organization_members',
    'assets',
    'asset_data_raw',
    'asset_specs_reconciled'
  )
order by tablename, policyname;
