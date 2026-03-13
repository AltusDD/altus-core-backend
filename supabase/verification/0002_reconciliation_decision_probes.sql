-- Focused non-destructive probes for canonical reconciliation decisions.

select table_name, column_name, data_type
from information_schema.columns
where table_schema = 'public'
  and (
    (table_name = 'assets' and column_name in ('name', 'display_name', 'external_ids'))
    or (table_name = 'asset_data_raw' and column_name in (
      'organization_id',
      'payload',
      'payload_jsonb',
      'fetched_at',
      'created_at',
      'payload_sha256',
      'source_record_id'
    ))
    or (table_name = 'asset_specs_reconciled' and column_name in (
      'organization_id',
      'spec_version',
      'id',
      'specs',
      'provenance',
      'effective_at',
      'created_at'
    ))
  )
order by table_name, ordinal_position;

select schemaname, tablename, policyname, permissive, roles, cmd
from pg_policies
where schemaname = 'public'
  and tablename = 'assets'
order by policyname;
