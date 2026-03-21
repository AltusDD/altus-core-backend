from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_SUPPORTED_SOURCES = ("MLS", "CORELOGIC", "FIELD", "DROPBOX", "ZIPFORMS", "MANUAL")


@dataclass(frozen=True)
class _SupabaseRestConfig:
    url: str
    service_role_key: str


class PropertyCockpitBackingSource(Protocol):
    def read_payload(self, asset_id: str, deal_id: str | None, transaction_id: str | None) -> dict[str, Any] | None:
        ...


class _NoopPropertyCockpitBackingSource:
    def read_payload(self, asset_id: str, deal_id: str | None, transaction_id: str | None) -> dict[str, Any] | None:
        return None


class _SupabasePropertyCockpitBackingSource:
    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key

    def read_payload(self, asset_id: str, deal_id: str | None, transaction_id: str | None) -> dict[str, Any] | None:
        asset_row = self._read_single_row(
            "assets",
            {
                "select": "id,organization_id,display_name,status,external_ids",
                "id": f"eq.{asset_id}",
                "limit": "1",
            },
        )
        if asset_row is None:
            return None

        property_row = self._read_single_row(
            "properties",
            {
                "select": "id,reconciliation_status,unresolved_conflict_count,active_manual_override_count,last_reconciled_at",
                "asset_id": f"eq.{asset_id}",
                "limit": "1",
            },
        )
        property_id = _as_optional_string(property_row.get("id")) if property_row else asset_id

        source_rows = self._read_rows(
            "asset_data_raw",
            {
                "select": "id,source,fetched_at",
                "asset_id": f"eq.{asset_id}",
                "order": "fetched_at.desc",
                "limit": "200",
            },
        )

        source_header = self._build_source_header_summary(source_rows)
        reconciliation = self._build_reconciliation_summary(property_row, property_id)
        evidence_media = self._build_evidence_media_summary(property_id)
        checklist_summary = self._build_transaction_document_checklist_summary(property_id, deal_id, transaction_id)
        client_visible_summary = self._build_client_visible_file_summary(property_id)

        evidence_sources = set(source_header["evidenceSources"])
        evidence_sources.update(evidence_media["sourceTypesPresent"])
        for artifact in client_visible_summary["artifacts"]:
            source_type = artifact.get("sourceType")
            if source_type in _SUPPORTED_SOURCES:
                evidence_sources.add(source_type)
        source_header["evidenceSources"] = sorted(evidence_sources, key=_source_sort_key)

        organization_id = _as_optional_string(asset_row.get("organization_id"))
        return {
            "propertyId": property_id,
            "assetId": asset_id,
            "organizationId": organization_id,
            "dealId": deal_id,
            "transactionId": transaction_id,
            "sourceHeaderSummary": source_header,
            "reconciliationSummary": reconciliation,
            "evidenceMediaSummary": evidence_media,
            "transactionDocumentChecklistSummary": checklist_summary,
            "clientVisibleFileSummary": client_visible_summary,
        }

    def _build_source_header_summary(self, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
        latest_by_source: dict[str, dict[str, Any]] = {}
        for row in source_rows:
            source_type = _normalize_source_type(row.get("source"))
            if source_type not in _SUPPORTED_SOURCES:
                continue
            if source_type not in latest_by_source:
                latest_by_source[source_type] = row

        structured_sources = []
        for source_type in _SUPPORTED_SOURCES:
            row = latest_by_source.get(source_type)
            if row is None:
                continue

            observed_at = _as_optional_string(row.get("fetched_at"))
            age_days = _age_days(observed_at)
            structured_sources.append(
                {
                    "sourceType": source_type,
                    "latestSourceImportId": _as_optional_string(row.get("id")),
                    "latestSourceRecordId": None,
                    "observedAt": observed_at,
                    "freshnessStatus": _freshness_status(age_days, observed_at),
                    "ageDays": age_days,
                    "recordCount": sum(
                        1 for candidate in source_rows if _normalize_source_type(candidate.get("source")) == source_type
                    ),
                }
            )

        return {
            "structuredSources": structured_sources,
            "evidenceSources": [item["sourceType"] for item in structured_sources],
        }

    def _build_reconciliation_summary(self, property_row: dict[str, Any] | None, property_id: str) -> dict[str, Any]:
        unresolved_conflict_count = _as_optional_int(_dict_get(property_row, "unresolved_conflict_count"))
        active_manual_override_count = _as_optional_int(_dict_get(property_row, "active_manual_override_count"))
        last_reconciled_at = _as_optional_string(_dict_get(property_row, "last_reconciled_at"))
        reconciliation_status = _as_optional_string(_dict_get(property_row, "reconciliation_status"))

        if unresolved_conflict_count is None:
            conflict_rows = self._read_rows(
                "property_reconciliation_status",
                {
                    "select": "id",
                    "property_id": f"eq.{property_id}",
                    "conflict_flag": "eq.true",
                    "limit": "500",
                },
            )
            if conflict_rows:
                unresolved_conflict_count = len(conflict_rows)

        if active_manual_override_count is None:
            override_rows = self._read_rows(
                "property_manual_overrides",
                {
                    "select": "id",
                    "property_id": f"eq.{property_id}",
                    "is_active": "eq.true",
                    "limit": "500",
                },
            )
            if override_rows:
                active_manual_override_count = len(override_rows)

        return {
            "reconciliationStatus": reconciliation_status,
            "unresolvedConflictCount": unresolved_conflict_count,
            "activeManualOverrideCount": active_manual_override_count,
            "lastReconciledAt": last_reconciled_at,
        }

    def _build_evidence_media_summary(self, property_id: str) -> dict[str, Any]:
        source_import_rows = self._read_rows(
            "property_source_imports",
            {
                "select": "id,source_type,ingested_at,source_timestamp",
                "property_id": f"eq.{property_id}",
                "order": "ingested_at.desc",
                "limit": "200",
            },
        )
        media_rows = self._read_rows(
            "property_source_media",
            {
                "select": "id,source_type,is_primary",
                "property_id": f"eq.{property_id}",
                "limit": "500",
            },
        )
        evidence_rows = self._read_rows(
            "property_evidence_records",
            {
                "select": "id,source_type,evidence_domain,document_class,observed_at",
                "property_id": f"eq.{property_id}",
                "limit": "500",
            },
        )
        storage_rows = self._read_rows(
            "property_file_storage_references",
            {
                "select": "id,storage_provider,verified_at",
                "property_id": f"eq.{property_id}",
                "limit": "500",
            },
        )

        latest_mls_snapshot_id = None
        latest_corelogic_snapshot_id = None
        if source_import_rows:
            for row in source_import_rows:
                source_type = _normalize_source_type(row.get("source_type"))
                if source_type == "MLS" and latest_mls_snapshot_id is None:
                    latest_mls_snapshot_id = _as_optional_string(row.get("id"))
                elif source_type == "CORELOGIC" and latest_corelogic_snapshot_id is None:
                    latest_corelogic_snapshot_id = _as_optional_string(row.get("id"))

        listing_media_count = 0
        has_primary_photo = False
        source_types_present: set[str] = set()
        for row in media_rows:
            listing_media_count += 1
            if row.get("is_primary") is True:
                has_primary_photo = True
            source_type = _normalize_source_type(row.get("source_type"))
            if source_type in _SUPPORTED_SOURCES:
                source_types_present.add(source_type)

        field_photo_count = 0
        field_document_count = 0
        last_captured_at = None
        for row in evidence_rows:
            source_type = _normalize_source_type(row.get("source_type"))
            if source_type in _SUPPORTED_SOURCES:
                source_types_present.add(source_type)
            evidence_domain = _as_optional_string(row.get("evidence_domain"))
            document_class = _as_optional_string(row.get("document_class"))
            observed_at = _as_optional_string(row.get("observed_at"))
            if evidence_domain == "fieldEvidence":
                if document_class == "field_photos":
                    field_photo_count += 1
                else:
                    field_document_count += 1
                last_captured_at = _max_timestamp(last_captured_at, observed_at)

        dropbox_file_count = 0
        verified_reference_count = 0
        for row in storage_rows:
            provider = _normalize_source_type(row.get("storage_provider"))
            if provider == "DROPBOX":
                dropbox_file_count += 1
                source_types_present.add("DROPBOX")
            if row.get("verified_at") is not None:
                verified_reference_count += 1

        return {
            "importedStructuredData": {
                "latestMlsSnapshotId": latest_mls_snapshot_id,
                "latestCorelogicSnapshotId": latest_corelogic_snapshot_id,
            },
            "importedMedia": {
                "listingMediaCount": listing_media_count,
                "hasPrimaryPhoto": has_primary_photo,
            },
            "fieldEvidence": {
                "fieldPhotoCount": field_photo_count,
                "fieldDocumentCount": field_document_count,
                "lastCapturedAt": last_captured_at,
            },
            "fileStorageReferences": {
                "dropboxFileCount": dropbox_file_count,
                "verifiedReferenceCount": verified_reference_count,
            },
            "sourceTypesPresent": sorted(source_types_present, key=_source_sort_key),
        }

    def _build_transaction_document_checklist_summary(
        self,
        property_id: str,
        deal_id: str | None,
        transaction_id: str | None,
    ) -> dict[str, Any]:
        checklist_rows = self._read_rows(
            "property_transaction_document_checklists",
            _compact_params(
                {
                    "select": (
                        "id,checklist_status,required_item_count,received_item_count,"
                        "missing_item_count,needs_review_item_count,approved_item_count"
                    ),
                    "property_id": f"eq.{property_id}",
                    "deal_id": f"eq.{deal_id}" if deal_id else None,
                    "transaction_id": f"eq.{transaction_id}" if transaction_id else None,
                    "order": "updated_at.desc",
                    "limit": "1",
                }
            ),
        )
        if not checklist_rows:
            return {
                "checklistStatus": None,
                "requiredItemCount": 0,
                "receivedItemCount": 0,
                "missingItemCount": 0,
                "needsReviewItemCount": 0,
                "approvedItemCount": 0,
                "groups": [],
            }

        checklist = checklist_rows[0]
        checklist_id = _as_optional_string(checklist.get("id"))
        item_rows = []
        if checklist_id:
            item_rows = self._read_rows(
                "property_transaction_checklist_items",
                {
                    "select": "checklist_group,document_state,linked_property_evidence_id",
                    "transaction_checklist_id": f"eq.{checklist_id}",
                    "limit": "500",
                },
            )

        groups = [
            {
                "checklistGroup": _as_optional_string(row.get("checklist_group")),
                "documentState": _as_optional_string(row.get("document_state")),
                "linkedEvidenceId": _as_optional_string(row.get("linked_property_evidence_id")),
            }
            for row in item_rows
            if _as_optional_string(row.get("checklist_group"))
        ]

        return {
            "checklistStatus": _as_optional_string(checklist.get("checklist_status")),
            "requiredItemCount": _as_optional_int(checklist.get("required_item_count")) or 0,
            "receivedItemCount": _as_optional_int(checklist.get("received_item_count")) or 0,
            "missingItemCount": _as_optional_int(checklist.get("missing_item_count")) or 0,
            "needsReviewItemCount": _as_optional_int(checklist.get("needs_review_item_count")) or 0,
            "approvedItemCount": _as_optional_int(checklist.get("approved_item_count")) or 0,
            "groups": groups,
        }

    def _build_client_visible_file_summary(self, property_id: str) -> dict[str, Any]:
        artifact_rows = self._read_rows(
            "property_client_visible_artifacts",
            {
                "select": "property_evidence_id,artifact_type,artifact_status,visibility_scope,expires_at,source_type",
                "property_id": f"eq.{property_id}",
                "limit": "500",
            },
        )

        artifacts = []
        client_visible_count = 0
        investor_visible_count = 0
        expiring_share_count = 0
        for row in artifact_rows:
            visibility_scope = _as_optional_string(row.get("visibility_scope"))
            expires_at = _as_optional_string(row.get("expires_at"))
            source_type = _normalize_source_type(row.get("source_type"))
            if visibility_scope == "client_visible":
                client_visible_count += 1
            if visibility_scope == "investor_visible":
                investor_visible_count += 1
            if visibility_scope == "expiring_share":
                expiring_share_count += 1
            artifacts.append(
                {
                    "propertyEvidenceId": _as_optional_string(row.get("property_evidence_id")),
                    "artifactType": _as_optional_string(row.get("artifact_type")),
                    "artifactStatus": _as_optional_string(row.get("artifact_status")),
                    "visibilityScope": visibility_scope,
                    "expiresAt": expires_at,
                    "sourceType": source_type if source_type in _SUPPORTED_SOURCES else None,
                }
            )

        return {
            "clientVisibleCount": client_visible_count,
            "investorVisibleCount": investor_visible_count,
            "expiringShareCount": expiring_share_count,
            "artifacts": artifacts,
        }

    def _read_single_row(self, table: str, params: dict[str, str]) -> dict[str, Any] | None:
        rows = self._read_rows(table, params)
        if not rows:
            return None
        first = rows[0]
        return first if isinstance(first, dict) else None

    def _read_rows(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        headers = {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
        }
        request = Request(
            f"{self._supabase_url}/rest/v1/{table}?{urlencode(params)}",
            headers=headers,
            method="GET",
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError, UnicodeDecodeError):
            return []

        if not isinstance(payload, list):
            return []

        return [row for row in payload if isinstance(row, dict)]


def build_property_cockpit(asset_id: str, deal_id: str | None, transaction_id: str | None) -> dict[str, Any]:
    fallback = _build_empty_property_cockpit(asset_id, deal_id, transaction_id)
    backing_payload = _build_default_backing_source().read_payload(asset_id, deal_id, transaction_id)
    if backing_payload is None:
        return fallback

    return {"data": backing_payload}


def _build_default_backing_source() -> PropertyCockpitBackingSource:
    supabase_config = _resolve_supabase_rest_config()
    if supabase_config is None:
        return _NoopPropertyCockpitBackingSource()

    return _SupabasePropertyCockpitBackingSource(
        supabase_config.url,
        supabase_config.service_role_key,
    )


def _resolve_supabase_rest_config() -> _SupabaseRestConfig | None:
    supabase_url = (
        os.getenv("ALTUS_ECC_PROPERTY_COCKPIT_SUPABASE_URL", "").strip()
        or os.getenv("SUPABASE_URL", "").strip()
    )
    service_role_key = (
        os.getenv("ALTUS_ECC_PROPERTY_COCKPIT_SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    if not supabase_url or not service_role_key:
        return None

    return _SupabaseRestConfig(url=supabase_url, service_role_key=service_role_key)


def _build_empty_property_cockpit(
    asset_id: str,
    deal_id: str | None,
    transaction_id: str | None,
) -> dict[str, Any]:
    return {
        "data": {
            "propertyId": asset_id,
            "assetId": asset_id,
            "organizationId": None,
            "dealId": deal_id,
            "transactionId": transaction_id,
            "sourceHeaderSummary": {
                "structuredSources": [],
                "evidenceSources": [],
            },
            "reconciliationSummary": {
                "reconciliationStatus": None,
                "unresolvedConflictCount": None,
                "activeManualOverrideCount": None,
                "lastReconciledAt": None,
            },
            "evidenceMediaSummary": {
                "importedStructuredData": {
                    "latestMlsSnapshotId": None,
                    "latestCorelogicSnapshotId": None,
                },
                "importedMedia": {
                    "listingMediaCount": 0,
                    "hasPrimaryPhoto": False,
                },
                "fieldEvidence": {
                    "fieldPhotoCount": 0,
                    "fieldDocumentCount": 0,
                    "lastCapturedAt": None,
                },
                "fileStorageReferences": {
                    "dropboxFileCount": 0,
                    "verifiedReferenceCount": 0,
                },
                "sourceTypesPresent": [],
            },
            "transactionDocumentChecklistSummary": {
                "checklistStatus": None,
                "requiredItemCount": 0,
                "receivedItemCount": 0,
                "missingItemCount": 0,
                "needsReviewItemCount": 0,
                "approvedItemCount": 0,
                "groups": [],
            },
            "clientVisibleFileSummary": {
                "clientVisibleCount": 0,
                "investorVisibleCount": 0,
                "expiringShareCount": 0,
                "artifacts": [],
            },
        }
    }


def _normalize_source_type(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    if normalized in {"CORELOGIC", "MLS", "FIELD", "DROPBOX", "ZIPFORMS", "MANUAL"}:
        return normalized
    return normalized


def _source_sort_key(source_type: str) -> int:
    try:
        return _SUPPORTED_SOURCES.index(source_type)
    except ValueError:
        return len(_SUPPORTED_SOURCES)


def _as_optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dict_get(row: dict[str, Any] | None, key: str) -> Any:
    if row is None:
        return None
    return row.get(key)


def _compact_params(params: dict[str, str | None]) -> dict[str, str]:
    return {key: value for key, value in params.items() if value is not None}


def _age_days(iso_timestamp: str | None) -> int | None:
    if not iso_timestamp:
        return None
    try:
        normalized = iso_timestamp.replace("Z", "+00:00")
        observed_at = datetime.fromisoformat(normalized)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)
        delta = datetime.now(tz=UTC) - observed_at.astimezone(UTC)
        return max(0, delta.days)
    except ValueError:
        return None


def _freshness_status(age_days: int | None, observed_at: str | None) -> str:
    if observed_at is None or age_days is None:
        return "unknown"
    if age_days <= 2:
        return "fresh"
    if age_days <= 14:
        return "aging"
    return "stale"


def _max_timestamp(current_value: str | None, candidate: str | None) -> str | None:
    if candidate is None:
        return current_value
    if current_value is None:
        return candidate
    return max(current_value, candidate)
