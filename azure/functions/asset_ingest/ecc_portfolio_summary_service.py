from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PortfolioSummaryBackingFields:
    asset_count: int | None = None


@dataclass(frozen=True)
class _SupabaseRestConfig:
    url: str
    service_role_key: str


class PortfolioSummaryBackingSource(Protocol):
    def read_fields(self, portfolio_id: str, as_of: str | None) -> PortfolioSummaryBackingFields | None:
        ...


class _NoopPortfolioSummaryBackingSource:
    def read_fields(self, portfolio_id: str, as_of: str | None) -> PortfolioSummaryBackingFields | None:
        return None


class _AssetsExternalIdsPortfolioCohortResolver:
    def __init__(self, supabase_url: str, service_role_key: str, external_ids_key: str) -> None:
        self._supabase_url = supabase_url.rstrip('/')
        self._service_role_key = service_role_key
        self._external_ids_key = external_ids_key

    def read_fields(self, portfolio_id: str, as_of: str | None) -> PortfolioSummaryBackingFields | None:
        headers = {
            'apikey': self._service_role_key,
            'Authorization': f'Bearer {self._service_role_key}',
            'Prefer': 'count=exact',
            'Range': '0-0',
        }
        params = {
            'select': 'id',
            f'external_ids->>{self._external_ids_key}': f'eq.{portfolio_id}',
        }

        query = urlencode(params)
        request = Request(
            f'{self._supabase_url}/rest/v1/assets?{query}',
            headers=headers,
            method='GET',
        )

        try:
            with urlopen(request, timeout=10) as response:
                content_range = response.headers.get('Content-Range', '')
        except (HTTPError, URLError):
            return None
        if '/' not in content_range:
            return None

        total_text = content_range.rsplit('/', 1)[1].strip()
        if total_text in {'', '*'}:
            return None

        try:
            return PortfolioSummaryBackingFields(asset_count=int(total_text))
        except ValueError:
            return None


def build_portfolio_summary(portfolio_id: str, as_of: str | None) -> dict[str, Any]:
    summary = _build_stub_portfolio_summary(portfolio_id, as_of)
    backing_fields = _build_default_backing_source().read_fields(portfolio_id, as_of)
    if backing_fields is None:
        return summary

    if backing_fields.asset_count is not None:
        summary['assetCount'] = backing_fields.asset_count
    return summary


def _build_default_backing_source() -> PortfolioSummaryBackingSource:
    external_ids_key = os.getenv('ALTUS_ECC_PORTFOLIO_SUMMARY_PORTFOLIO_ID_EXTERNAL_IDS_KEY', '').strip()
    supabase_config = _resolve_supabase_rest_config()
    if not external_ids_key or supabase_config is None:
        return _NoopPortfolioSummaryBackingSource()

    return _AssetsExternalIdsPortfolioCohortResolver(
        supabase_config.url,
        supabase_config.service_role_key,
        external_ids_key,
    )


def _resolve_supabase_rest_config() -> _SupabaseRestConfig | None:
    supabase_url = (
        os.getenv('ALTUS_ECC_PORTFOLIO_SUMMARY_SUPABASE_URL', '').strip()
        or os.getenv('SUPABASE_URL', '').strip()
    )
    service_role_key = (
        os.getenv('ALTUS_ECC_PORTFOLIO_SUMMARY_SUPABASE_SERVICE_ROLE_KEY', '').strip()
        or os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    )
    if not supabase_url or not service_role_key:
        return None

    return _SupabaseRestConfig(url=supabase_url, service_role_key=service_role_key)


def _build_stub_portfolio_summary(portfolio_id: str, as_of: str | None) -> dict[str, Any]:
    seed = sum(ord(character) for character in portfolio_id)
    asset_count = (seed % 18) + 3
    total_units = asset_count * 4
    occupied_units = min(total_units, max(0, total_units - (seed % 7)))
    occupancy_rate = occupied_units / total_units if total_units else 0.0
    estimated_value = Decimal(asset_count) * Decimal('125000.00')

    return {
        'portfolioId': portfolio_id,
        'asOfDate': as_of,
        'assetCount': asset_count,
        'occupiedUnits': occupied_units,
        'totalUnits': total_units,
        'occupancyRate': occupancy_rate,
        'estimatedValue': float(estimated_value),
        'currency': 'USD',
        'activeAlerts': seed % 4,
        'status': 'stub_ready',
    }


