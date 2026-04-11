from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PortfolioAssetsBackingRow:
    asset_id: str
    display_name: str | None = None
    asset_type: str | None = None
    status: str | None = None
    total_units: int | None = None


@dataclass(frozen=True)
class PortfolioAssetsBackingPayload:
    rows: list[PortfolioAssetsBackingRow]
    total: int


@dataclass(frozen=True)
class _SupabaseRestConfig:
    url: str
    service_role_key: str


class PortfolioAssetsBackingSource(Protocol):
    def read_rows(self, portfolio_id: str, limit: int, offset: int) -> PortfolioAssetsBackingPayload | None:
        ...


class _NoopPortfolioAssetsBackingSource:
    def read_rows(self, portfolio_id: str, limit: int, offset: int) -> PortfolioAssetsBackingPayload | None:
        return None


class _AssetsExternalIdsPortfolioAssetsSource:
    def __init__(self, supabase_url: str, service_role_key: str, external_ids_key: str) -> None:
        self._supabase_url = supabase_url.rstrip('/')
        self._service_role_key = service_role_key
        self._external_ids_key = external_ids_key

    def read_rows(self, portfolio_id: str, limit: int, offset: int) -> PortfolioAssetsBackingPayload | None:
        asset_rows, total = self._read_asset_page(portfolio_id, limit, offset)
        if asset_rows is None or total is None:
            return None

        units_by_asset_id = self._read_units_by_asset_id(asset_rows)
        rows = [
            PortfolioAssetsBackingRow(
                asset_id=str(row['id']),
                display_name=_as_optional_string(row.get('display_name')),
                asset_type=_as_optional_string(row.get('asset_type')),
                status=_as_optional_string(row.get('status')),
                total_units=units_by_asset_id.get(str(row['id'])),
            )
            for row in asset_rows
        ]
        return PortfolioAssetsBackingPayload(rows=rows, total=total)

    def _read_asset_page(
        self, portfolio_id: str, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]] | None, int | None]:
        headers = {
            'apikey': self._service_role_key,
            'Authorization': f'Bearer {self._service_role_key}',
            'Prefer': 'count=exact',
        }
        params = {
            'select': 'id,display_name,asset_type,status',
            f'external_ids->>{self._external_ids_key}': f'eq.{portfolio_id}',
            'order': 'id.asc',
            'limit': str(limit),
            'offset': str(offset),
        }
        request = Request(
            f'{self._supabase_url}/rest/v1/assets?{urlencode(params)}',
            headers=headers,
            method='GET',
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode('utf-8'))
                content_range = response.headers.get('Content-Range', '')
        except (HTTPError, URLError, json.JSONDecodeError, UnicodeDecodeError):
            return None, None

        if not isinstance(payload, list):
            return None, None
        if '/' not in content_range:
            return None, None

        total_text = content_range.rsplit('/', 1)[1].strip()
        if total_text in {'', '*'}:
            return None, None

        try:
            total = int(total_text)
        except ValueError:
            return None, None

        for row in payload:
            if not isinstance(row, dict) or not row.get('id'):
                return None, None
        return payload, total

    def _read_units_by_asset_id(self, asset_rows: list[dict[str, Any]]) -> dict[str, int | None]:
        asset_ids = [str(row['id']) for row in asset_rows if row.get('id')]
        if not asset_ids:
            return {}

        headers = {
            'apikey': self._service_role_key,
            'Authorization': f'Bearer {self._service_role_key}',
        }
        quoted_ids = ','.join(f'"{asset_id}"' for asset_id in asset_ids)
        params = {
            'select': 'asset_id,units_count',
            'asset_id': f'in.({quoted_ids})',
        }
        request = Request(
            f'{self._supabase_url}/rest/v1/asset_specs_reconciled?{urlencode(params)}',
            headers=headers,
            method='GET',
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode('utf-8'))
        except (HTTPError, URLError, json.JSONDecodeError, UnicodeDecodeError):
            return {}

        if not isinstance(payload, list):
            return {}

        units_by_asset_id: dict[str, int | None] = {}
        for row in payload:
            if not isinstance(row, dict):
                continue
            asset_id = row.get('asset_id')
            if asset_id is None:
                continue
            units_count = row.get('units_count')
            if units_count is None:
                units_by_asset_id[str(asset_id)] = None
                continue
            try:
                units_by_asset_id[str(asset_id)] = int(units_count)
            except (TypeError, ValueError):
                units_by_asset_id[str(asset_id)] = None

        return units_by_asset_id


def build_portfolio_assets(portfolio_id: str, limit: int, offset: int) -> dict[str, Any]:
    stub_payload = _build_stub_portfolio_assets(portfolio_id, limit, offset)
    backing_payload = _build_default_backing_source().read_rows(portfolio_id, limit, offset)
    if backing_payload is None:
        return stub_payload

    rows = []
    for index, backing_row in enumerate(backing_payload.rows):
        row = _build_stub_asset_row(portfolio_id, offset + index)
        row['assetId'] = backing_row.asset_id
        if backing_row.display_name is not None:
            row['displayName'] = backing_row.display_name
        if backing_row.asset_type is not None:
            row['assetType'] = backing_row.asset_type
        if backing_row.status is not None:
            row['status'] = backing_row.status
        if backing_row.total_units is not None:
            row['totalUnits'] = backing_row.total_units
        rows.append(row)

    return {
        'data': rows,
        'meta': {
            'portfolioId': portfolio_id,
            'limit': limit,
            'offset': offset,
            'total': backing_payload.total,
        },
    }


def _build_default_backing_source() -> PortfolioAssetsBackingSource:
    external_ids_key = os.getenv('ALTUS_ECC_PORTFOLIO_ASSETS_PORTFOLIO_ID_EXTERNAL_IDS_KEY', '').strip()
    supabase_config = _resolve_supabase_rest_config()
    if not external_ids_key or supabase_config is None:
        return _NoopPortfolioAssetsBackingSource()

    return _AssetsExternalIdsPortfolioAssetsSource(
        supabase_config.url,
        supabase_config.service_role_key,
        external_ids_key,
    )


def _resolve_supabase_rest_config() -> _SupabaseRestConfig | None:
    supabase_url = (
        os.getenv('ALTUS_ECC_PORTFOLIO_ASSETS_SUPABASE_URL', '').strip()
        or os.getenv('SUPABASE_URL', '').strip()
    )
    service_role_key = (
        os.getenv('ALTUS_ECC_PORTFOLIO_ASSETS_SUPABASE_SERVICE_ROLE_KEY', '').strip()
        or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    )
    if not supabase_url or not service_role_key:
        return None

    return _SupabaseRestConfig(url=supabase_url, service_role_key=service_role_key)


def _build_stub_portfolio_assets(portfolio_id: str, limit: int, offset: int) -> dict[str, Any]:
    base_seed = sum(ord(character) for character in portfolio_id)
    total = 12 + (base_seed % 9)
    rows = [
        _build_stub_asset_row(portfolio_id, index)
        for index in range(offset, min(offset + limit, total))
    ]

    return {
        'data': rows,
        'meta': {
            'portfolioId': portfolio_id,
            'limit': limit,
            'offset': offset,
            'total': total,
        },
    }


def _build_stub_asset_row(portfolio_id: str, index: int) -> dict[str, Any]:
    base_seed = sum(ord(character) for character in portfolio_id)
    units = 4 + ((base_seed + index) % 8)
    occupied_units = max(0, units - ((base_seed + index) % 3))
    return {
        'assetId': f'{portfolio_id}-asset-{index + 1:03d}',
        'portfolioId': portfolio_id,
        'displayName': f'Portfolio Asset {index + 1}',
        'assetType': 'multifamily',
        'status': 'stub_ready',
        'occupiedUnits': occupied_units,
        'totalUnits': units,
        'occupancyRate': occupied_units / units if units else 0.0,
        'marketValue': float((index + 1) * 100000),
        'city': None,
        'state': None,
    }


def _as_optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
