import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import azure.functions as func
import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_ALLOWED_SOURCES = {"CORELOGIC", "MLS", "DOORLOOP", "MANUAL", "OTHER"}
_ALLOWED_LINK_TYPES = {
    "parcel_structure",
    "structure_unit",
    "asset_deal",
    "portfolio_asset",
    "deal_asset",
    "asset_portfolio",
    "parcel_unit",
    "structure_deal",
}
_LINK_SOURCE_PREFIX = "ASSET_LINK::"


class RuntimeConfig:
    def __init__(self) -> None:
        self.config_mode = "UNKNOWN"
        env_supabase_url = os.getenv("SUPABASE_URL")
        env_supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if env_supabase_url and env_supabase_service_role_key:
            self.supabase_url = env_supabase_url.rstrip("/")
            self.supabase_service_role_key = env_supabase_service_role_key
            self.config_mode = "ENV"
            return

        vault_url = os.getenv("KEY_VAULT_URL", "https://altus-core-staging-kv.vault.azure.net/")
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=vault_url, credential=credential)

        if env_supabase_url:
            self.supabase_url = env_supabase_url.rstrip("/")
        else:
            self.supabase_url = secret_client.get_secret("SUPABASE-URL").value.rstrip("/")

        if env_supabase_service_role_key:
            self.supabase_service_role_key = env_supabase_service_role_key
        else:
            self.supabase_service_role_key = secret_client.get_secret("SUPABASE-SERVICE-ROLE-KEY").value
        
        self.config_mode = "KV"


_config: RuntimeConfig | None = None


def _build_headers() -> dict[str, str]:
    build_sha = os.getenv("ALTUS_BUILD_SHA", "unknown")
    cfg_mode = _config.config_mode if _config else "UNKNOWN"
    return {
        "x-altus-build-sha": build_sha,
        "x-altus-config-mode": cfg_mode
    }


def _get_config() -> RuntimeConfig:
    global _config
    if _config is None:
        _config = RuntimeConfig()
    return _config


def _canonicalize_and_hash(raw_payload: Any) -> tuple[str, str]:
    canonical = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return canonical, payload_hash


def _insert_supabase_row(table: str, payload: dict[str, Any], config: RuntimeConfig) -> dict[str, Any]:
    endpoint = f"{config.supabase_url}/rest/v1/{table}"
    headers = {
        "apikey": config.supabase_service_role_key,
        "Authorization": f"Bearer {config.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase insert failed for {table}: {response.status_code} {response.text}")

    data = response.json()
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"Supabase insert returned no rows for {table}")

    return data[0]


def _delete_supabase_row_by_id(table: str, row_id: str, config: RuntimeConfig) -> None:
    endpoint = f"{config.supabase_url}/rest/v1/{table}?id=eq.{row_id}"
    headers = {
        "apikey": config.supabase_service_role_key,
        "Authorization": f"Bearer {config.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    resp = requests.delete(endpoint, headers=headers, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase delete failed for {table} id={row_id}: {resp.status_code} {resp.text}")


def _mark_asset_error(asset_id: str, config: RuntimeConfig) -> None:
    endpoint = f"{config.supabase_url}/rest/v1/assets?id=eq.{asset_id}"
    headers = {
        "apikey": config.supabase_service_role_key,
        "Authorization": f"Bearer {config.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    resp = requests.patch(endpoint, headers=headers, json={"status": "ERROR"}, timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Supabase patch failed for assets id={asset_id}: {resp.status_code} {resp.text}")


def _supabase_get_rows(table: str, params: dict[str, str], config: RuntimeConfig) -> list[dict[str, Any]]:
    endpoint = f"{config.supabase_url}/rest/v1/{table}"
    headers = {
        "apikey": config.supabase_service_role_key,
        "Authorization": f"Bearer {config.supabase_service_role_key}",
    }
    response = requests.get(endpoint, headers=headers, params=params, timeout=30)
    if response.status_code >= 400:
        raise RuntimeError(f"Supabase select failed for {table}: {response.status_code} {response.text}")

    data = response.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Supabase select returned non-list for {table}")
    return data


def _not_found(code: str, message: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": code,
                "error": message,
                "status": 404,
            }
        ),
        status_code=404,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _require_org_id(req: func.HttpRequest) -> tuple[str | None, func.HttpResponse | None]:
    org_id_raw = req.headers.get("x-altus-org-id")
    if not org_id_raw:
        return None, _bad_request("Missing required header: x-altus-org-id")

    try:
        organization_id = str(uuid.UUID(org_id_raw))
        return organization_id, None
    except ValueError:
        return None, _bad_request("x-altus-org-id must be a valid UUID")


def _bad_request(message: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"ok": False, "error": message}),
        status_code=400,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _internal_error() -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": "INGEST_INTERNAL",
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _stage_error(code: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": code,
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _asset_enrich_internal_error() -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": "ASSET_ENRICH_INTERNAL",
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _asset_search_internal_error() -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": "ASSET_SEARCH_INTERNAL",
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _asset_match_internal_error() -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": "ASSET_MATCH_INTERNAL",
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _asset_link_internal_error() -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(
            {
                "ok": False,
                "code": "ASSET_LINK_INTERNAL",
                "error": "Internal server error",
                "status": 500,
            }
        ),
        status_code=500,
        headers=_build_headers(),
        mimetype="application/json",
    )


def _extract_link_payload(req: func.HttpRequest) -> tuple[dict[str, str] | None, func.HttpResponse | None]:
    try:
        body = req.get_json()
    except ValueError:
        return None, _bad_request("Invalid payload")

    if not isinstance(body, dict):
        return None, _bad_request("Invalid payload")

    parent_asset_id_raw = body.get("parent_asset_id")
    child_asset_id_raw = body.get("child_asset_id")
    link_type_raw = body.get("link_type")

    if not isinstance(parent_asset_id_raw, str) or not isinstance(child_asset_id_raw, str) or not isinstance(link_type_raw, str):
        return None, _bad_request("Invalid payload")

    try:
        parent_asset_id = str(uuid.UUID(parent_asset_id_raw))
        child_asset_id = str(uuid.UUID(child_asset_id_raw))
    except ValueError:
        return None, _bad_request("Invalid payload")

    link_type = link_type_raw.strip()
    if not link_type:
        return None, _bad_request("Invalid payload")

    if parent_asset_id == child_asset_id:
        return None, _bad_request("Invalid payload")

    if link_type not in _ALLOWED_LINK_TYPES:
        return None, _bad_request("Invalid payload")

    return {
        "parent_asset_id": parent_asset_id,
        "child_asset_id": child_asset_id,
        "link_type": link_type,
    }, None


def _is_missing_asset_links_table_error(exc: Exception) -> bool:
    message = str(exc)
    return "public.asset_links" in message and "PGRST205" in message


def _get_fallback_link_rows(
    organization_id: str,
    parent_asset_id: str,
    child_asset_id: str,
    link_type: str,
    config: RuntimeConfig,
) -> list[dict[str, Any]]:
    source_value = f"{_LINK_SOURCE_PREFIX}{link_type}"
    raw_rows = _supabase_get_rows(
        "asset_data_raw",
        {
            "select": "id,asset_id,source,payload_jsonb,created_at",
            "asset_id": f"eq.{parent_asset_id}",
            "source": f"eq.{source_value}",
            "order": "created_at.desc",
            "limit": "200",
        },
        config,
    )

    matches: list[dict[str, Any]] = []
    for row in raw_rows:
        payload = row.get("payload_jsonb")
        if not isinstance(payload, dict):
            continue

        if payload.get("record_type") != "asset_link":
            continue
        if payload.get("organization_id") != organization_id:
            continue
        if payload.get("parent_asset_id") != parent_asset_id:
            continue
        if payload.get("child_asset_id") != child_asset_id:
            continue
        if payload.get("link_type") != link_type:
            continue

        matches.append(row)

    return matches


def _fallback_create_link(
    organization_id: str,
    parent_asset_id: str,
    child_asset_id: str,
    link_type: str,
    config: RuntimeConfig,
) -> dict[str, Any]:
    fallback_rows = _get_fallback_link_rows(
        organization_id=organization_id,
        parent_asset_id=parent_asset_id,
        child_asset_id=child_asset_id,
        link_type=link_type,
        config=config,
    )

    if fallback_rows:
        row = fallback_rows[0]
        return {
            "id": row.get("id"),
            "parent_asset_id": parent_asset_id,
            "child_asset_id": child_asset_id,
            "link_type": link_type,
        }

    source_value = f"{_LINK_SOURCE_PREFIX}{link_type}"
    created_row = _insert_supabase_row(
        "asset_data_raw",
        {
            "asset_id": parent_asset_id,
            "source": source_value,
            "payload_jsonb": {
                "record_type": "asset_link",
                "organization_id": organization_id,
                "parent_asset_id": parent_asset_id,
                "child_asset_id": child_asset_id,
                "link_type": link_type,
            },
        },
        config,
    )

    return {
        "id": created_row.get("id"),
        "parent_asset_id": parent_asset_id,
        "child_asset_id": child_asset_id,
        "link_type": link_type,
    }


def _fallback_delete_link(
    organization_id: str,
    parent_asset_id: str,
    child_asset_id: str,
    link_type: str,
    config: RuntimeConfig,
) -> bool:
    fallback_rows = _get_fallback_link_rows(
        organization_id=organization_id,
        parent_asset_id=parent_asset_id,
        child_asset_id=child_asset_id,
        link_type=link_type,
        config=config,
    )

    if not fallback_rows:
        return False

    _delete_supabase_row_by_id("asset_data_raw", str(fallback_rows[0].get("id")), config)
    return True


@app.route(route="assets", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_list(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        limit_raw = req.params.get("limit", "50")
        offset_raw = req.params.get("offset", "0")

        try:
            limit = int(limit_raw)
            offset = int(offset_raw)
        except ValueError:
            return _bad_request("limit and offset must be integers")

        if limit < 1 or limit > 200:
            return _bad_request("limit must be between 1 and 200")
        if offset < 0:
            return _bad_request("offset must be >= 0")

        params: dict[str, str] = {
            "select": "*",
            "organization_id": f"eq.{organization_id}",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }

        status_value = req.params.get("status")
        if status_value:
            params["status"] = f"eq.{status_value}"

        asset_type_value = req.params.get("asset_type")
        if asset_type_value:
            params["asset_type"] = f"eq.{asset_type_value}"

        query_text = req.params.get("q")
        if query_text:
            safe_query = query_text.replace("*", "")
            params["or"] = f"(display_name.ilike.*{safe_query}*,name.ilike.*{safe_query}*)"

        config = _get_config()
        items = _supabase_get_rows("assets", params, config)

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "items": items,
                    "limit": limit,
                    "offset": offset,
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset list failed")
        return _internal_error()


@app.route(route="assets/search", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_search(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        limit_raw = req.params.get("limit", "25")
        offset_raw = req.params.get("offset", "0")

        try:
            limit = int(limit_raw)
            offset = int(offset_raw)
        except ValueError:
            return _bad_request("limit and offset must be integers")

        if limit < 1 or limit > 200:
            return _bad_request("limit must be between 1 and 200")
        if offset < 0:
            return _bad_request("offset must be >= 0")

        q_value = (req.params.get("q") or "").strip()
        apn_value = (req.params.get("apn") or "").strip()
        clip_value = (req.params.get("clip") or "").strip()

        params: dict[str, str] = {
            "select": "id,organization_id,asset_type,status,display_name,address_canonical,apn,clip,created_at,updated_at",
            "organization_id": f"eq.{organization_id}",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }

        if apn_value:
            params["apn"] = f"eq.{apn_value}"
        elif clip_value:
            params["clip"] = f"eq.{clip_value}"
        elif q_value:
            safe_query = q_value.replace("*", "").replace(",", "")
            params["or"] = f"(display_name.ilike.*{safe_query}*,address_canonical.ilike.*{safe_query}*)"

        config = _get_config()
        items = _supabase_get_rows("assets", params, config)

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "items": items,
                    "limit": limit,
                    "offset": offset,
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset search failed")
        return _asset_search_internal_error()


@app.route(route="assets/{asset_id}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def asset_detail(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        asset_id = req.route_params.get("asset_id")
        if not asset_id:
            return _bad_request("asset_id is required")

        try:
            normalized_asset_id = str(uuid.UUID(asset_id))
        except ValueError:
            return _bad_request("asset_id must be a valid UUID")

        config = _get_config()
        assets = _supabase_get_rows(
            "assets",
            {
                "select": "*",
                "id": f"eq.{normalized_asset_id}",
                "organization_id": f"eq.{organization_id}",
                "limit": "1",
            },
            config,
        )

        if not assets:
            return _not_found("ASSET_NOT_FOUND", "Asset not found")

        latest_raw: dict[str, Any] | None = None
        raw_queries = [
            {
                "select": "*",
                "asset_id": f"eq.{normalized_asset_id}",
                "order": "created_at.desc",
                "limit": "1",
            },
            {
                "select": "*",
                "asset_id": f"eq.{normalized_asset_id}",
                "order": "fetched_at.desc",
                "limit": "1",
            },
            {
                "select": "*",
                "asset_id": f"eq.{normalized_asset_id}",
                "order": "id.desc",
                "limit": "1",
            },
        ]
        for raw_query in raw_queries:
            try:
                raw_rows = _supabase_get_rows("asset_data_raw", raw_query, config)
                latest_raw = raw_rows[0] if raw_rows else None
                break
            except Exception:
                continue

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "asset": assets[0],
                    "latest_raw": latest_raw,
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset detail failed")
        return _internal_error()


@app.route(route="assets/match", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_match(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        try:
            body = req.get_json()
        except ValueError:
            return _bad_request("Invalid payload")

        if not isinstance(body, dict):
            return _bad_request("Invalid payload")

        asset = body.get("asset")
        if not isinstance(asset, dict):
            return _bad_request("Invalid payload")

        field_names = ["apn", "clip", "address_canonical", "display_name"]
        normalized_fields: dict[str, str] = {}
        for field_name in field_names:
            field_value = asset.get(field_name)
            if field_value is None:
                normalized_fields[field_name] = ""
                continue

            if not isinstance(field_value, str):
                return _bad_request("Invalid payload")

            normalized_fields[field_name] = field_value.strip()

        if not any(normalized_fields.values()):
            return _bad_request("Invalid payload")

        config = _get_config()
        projection = "id,organization_id,asset_type,status,display_name,address_canonical,apn,clip,created_at,updated_at"

        for strategy in field_names:
            strategy_value = normalized_fields[strategy]
            if not strategy_value:
                continue

            candidates = _supabase_get_rows(
                "assets",
                {
                    "select": projection,
                    "organization_id": f"eq.{organization_id}",
                    strategy: f"eq.{strategy_value}",
                    "order": "created_at.desc",
                },
                config,
            )

            if candidates:
                return func.HttpResponse(
                    json.dumps(
                        {
                            "ok": True,
                            "match_strategy": strategy,
                            "candidates": candidates,
                        }
                    ),
                    status_code=200,
                    headers=_build_headers(),
                    mimetype="application/json",
                )

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "match_strategy": "none",
                    "candidates": [],
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset match failed")
        return _asset_match_internal_error()


@app.route(route="assets/link", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_link_create(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        payload, payload_error = _extract_link_payload(req)
        if payload_error is not None:
            return payload_error

        parent_asset_id = payload["parent_asset_id"]
        child_asset_id = payload["child_asset_id"]
        link_type = payload["link_type"]
        config = _get_config()

        parent_rows = _supabase_get_rows(
            "assets",
            {
                "select": "id",
                "organization_id": f"eq.{organization_id}",
                "id": f"eq.{parent_asset_id}",
                "limit": "1",
            },
            config,
        )
        if not parent_rows:
            return _bad_request("Invalid payload")

        child_rows = _supabase_get_rows(
            "assets",
            {
                "select": "id",
                "organization_id": f"eq.{organization_id}",
                "id": f"eq.{child_asset_id}",
                "limit": "1",
            },
            config,
        )
        if not child_rows:
            return _bad_request("Invalid payload")

        try:
            existing_rows = _supabase_get_rows(
                "asset_links",
                {
                    "select": "id,parent_asset_id,child_asset_id,link_type",
                    "organization_id": f"eq.{organization_id}",
                    "parent_asset_id": f"eq.{parent_asset_id}",
                    "child_asset_id": f"eq.{child_asset_id}",
                    "link_type": f"eq.{link_type}",
                    "limit": "1",
                },
                config,
            )
        except RuntimeError as exc:
            if _is_missing_asset_links_table_error(exc):
                existing_rows = _get_fallback_link_rows(
                    organization_id=organization_id,
                    parent_asset_id=parent_asset_id,
                    child_asset_id=child_asset_id,
                    link_type=link_type,
                    config=config,
                )
            else:
                raise

        if existing_rows:
            existing_row = existing_rows[0]
            return func.HttpResponse(
                json.dumps(
                    {
                        "ok": True,
                        "link_id": existing_row.get("id"),
                        "parent_asset_id": existing_row.get("parent_asset_id"),
                        "child_asset_id": existing_row.get("child_asset_id"),
                        "link_type": existing_row.get("link_type"),
                    }
                ),
                status_code=200,
                headers=_build_headers(),
                mimetype="application/json",
            )

        try:
            created_row = _insert_supabase_row(
                "asset_links",
                {
                    "organization_id": organization_id,
                    "parent_asset_id": parent_asset_id,
                    "child_asset_id": child_asset_id,
                    "link_type": link_type,
                },
                config,
            )
        except RuntimeError as exc:
            if _is_missing_asset_links_table_error(exc):
                created_row = _fallback_create_link(
                    organization_id=organization_id,
                    parent_asset_id=parent_asset_id,
                    child_asset_id=child_asset_id,
                    link_type=link_type,
                    config=config,
                )
            else:
                raise

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "link_id": created_row.get("id"),
                    "parent_asset_id": created_row.get("parent_asset_id"),
                    "child_asset_id": created_row.get("child_asset_id"),
                    "link_type": created_row.get("link_type"),
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset link create failed")
        return _asset_link_internal_error()


@app.route(route="assets/link", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_link_delete(req: func.HttpRequest) -> func.HttpResponse:
    try:
        organization_id, error_response = _require_org_id(req)
        if error_response is not None:
            return error_response

        payload, payload_error = _extract_link_payload(req)
        if payload_error is not None:
            return payload_error

        parent_asset_id = payload["parent_asset_id"]
        child_asset_id = payload["child_asset_id"]
        link_type = payload["link_type"]
        config = _get_config()

        used_fallback = False
        try:
            matching_rows = _supabase_get_rows(
                "asset_links",
                {
                    "select": "id,parent_asset_id,child_asset_id,link_type",
                    "organization_id": f"eq.{organization_id}",
                    "parent_asset_id": f"eq.{parent_asset_id}",
                    "child_asset_id": f"eq.{child_asset_id}",
                    "link_type": f"eq.{link_type}",
                    "limit": "1",
                },
                config,
            )
        except RuntimeError as exc:
            if _is_missing_asset_links_table_error(exc):
                used_fallback = True
                matching_rows = _get_fallback_link_rows(
                    organization_id=organization_id,
                    parent_asset_id=parent_asset_id,
                    child_asset_id=child_asset_id,
                    link_type=link_type,
                    config=config,
                )
            else:
                raise

        if not matching_rows:
            return func.HttpResponse(
                json.dumps(
                    {
                        "ok": False,
                        "code": "ASSET_LINK_NOT_FOUND",
                    }
                ),
                status_code=404,
                headers=_build_headers(),
                mimetype="application/json",
            )

        if used_fallback:
            deleted = _fallback_delete_link(
                organization_id=organization_id,
                parent_asset_id=parent_asset_id,
                child_asset_id=child_asset_id,
                link_type=link_type,
                config=config,
            )
            if not deleted:
                return func.HttpResponse(
                    json.dumps(
                        {
                            "ok": False,
                            "code": "ASSET_LINK_NOT_FOUND",
                        }
                    ),
                    status_code=404,
                    headers=_build_headers(),
                    mimetype="application/json",
                )
        else:
            _delete_supabase_row_by_id("asset_links", str(matching_rows[0].get("id")), config)

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "deleted": True,
                    "parent_asset_id": parent_asset_id,
                    "child_asset_id": child_asset_id,
                    "link_type": link_type,
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("Asset link delete failed")
        return _asset_link_internal_error()


@app.route(route="assets/ingest", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def assets_ingest(req: func.HttpRequest) -> func.HttpResponse:
    try:
        org_id_raw = req.headers.get("x-altus-org-id")
        if not org_id_raw:
            return _bad_request("Missing required header: x-altus-org-id")

        try:
            organization_id = str(uuid.UUID(org_id_raw))
        except ValueError:
            return _bad_request("x-altus-org-id must be a valid UUID")

        try:
            body = req.get_json()
        except ValueError:
            return _bad_request("Invalid payload")

        if not isinstance(body, dict):
            return _bad_request("Invalid payload")

        config = _get_config()

        asset_id_candidate = body.get("asset_id")
        if asset_id_candidate:
            try:
                enrichment_asset_id = str(uuid.UUID(str(asset_id_candidate)))
            except ValueError:
                return _bad_request("Invalid payload")

            source_value = body.get("source") or "MANUAL"
            if not isinstance(source_value, str) or not source_value.strip():
                return _bad_request("Invalid payload")

            enrichment_payload = body.get("raw", body)

            try:
                existing_assets = _supabase_get_rows(
                    "assets",
                    {
                        "select": "id",
                        "id": f"eq.{enrichment_asset_id}",
                        "organization_id": f"eq.{organization_id}",
                        "limit": "1",
                    },
                    config,
                )
            except Exception:
                logging.exception("ASSET_ENRICH: asset existence check failed")
                return _asset_enrich_internal_error()

            if not existing_assets:
                return func.HttpResponse(
                    json.dumps({"ok": False, "error": "Asset not found"}),
                    status_code=404,
                    headers=_build_headers(),
                    mimetype="application/json",
                )

            raw_record_id = str(uuid.uuid4())
            fetched_at = datetime.now(timezone.utc).isoformat()
            try:
                _insert_supabase_row(
                    table="asset_data_raw",
                    payload={
                        "id": raw_record_id,
                        "asset_id": enrichment_asset_id,
                        "source": source_value,
                        "payload_jsonb": enrichment_payload,
                        "fetched_at": fetched_at,
                    },
                    config=config,
                )
            except Exception:
                logging.exception("ASSET_ENRICH: asset_data_raw insert failed")
                return _asset_enrich_internal_error()

            return func.HttpResponse(
                json.dumps(
                    {
                        "ok": True,
                        "asset_id": enrichment_asset_id,
                        "raw_record_id": raw_record_id,
                    }
                ),
                status_code=200,
                headers=_build_headers(),
                mimetype="application/json",
            )

        source = body.get("source")
        if source not in _ALLOWED_SOURCES:
            return _bad_request("source must be one of CORELOGIC|MLS|DOORLOOP|MANUAL|OTHER")

        if "raw" not in body:
            return _bad_request("raw is required")

        raw_payload = body.get("raw")
        if not isinstance(raw_payload, dict):
            return _bad_request("raw must be a JSON object")

        asset_obj = body.get("asset") or {}
        if not isinstance(asset_obj, dict):
            return _bad_request("asset must be a JSON object when provided")

        _, payload_hash = _canonicalize_and_hash(raw_payload)

        asset_type = asset_obj.get("asset_type") or "PROPERTY"
        status = asset_obj.get("status") or "ACTIVE"
        display_name = asset_obj.get("name") or f"{source}:{payload_hash[:12]}"

        try:
            asset_row = _insert_supabase_row(
                table="assets",
                payload={
                    "organization_id": organization_id,
                    "asset_type": asset_type,
                    "status": status,
                    "display_name": display_name,
                    "external_ids": {"payload_hash": payload_hash},
                },
                config=config,
            )
        except Exception:
            logging.exception("INGEST: Supabase assets insert failed")
            return _stage_error("INGEST_ASSET_INSERT_FAILED")

        asset_id = asset_row.get("id")
        if not asset_id:
            raise RuntimeError("assets insert did not return id")

        try:
            raw_row = _insert_supabase_row(
                table="asset_data_raw",
                payload={
                    "asset_id": asset_id,
                    "source": source,
                    "payload_jsonb": raw_payload,
                },
                config=config,
            )
        except Exception:
            logging.exception("INGEST: Supabase asset_data_raw insert failed (will compensate)")
            try:
                _delete_supabase_row_by_id("assets", str(asset_id), config)
            except Exception:
                logging.exception("INGEST: Compensation delete failed (will attempt mark ERROR)")
                try:
                    _mark_asset_error(str(asset_id), config)
                except Exception:
                    logging.exception("INGEST: Compensation mark ERROR failed")
            return _stage_error("INGEST_RAW_INSERT_FAILED")

        raw_id = raw_row.get("id")
        if not raw_id:
            raise RuntimeError("asset_data_raw insert did not return id")

        return func.HttpResponse(
            json.dumps(
                {
                    "ok": True,
                    "asset_id": str(asset_id),
                    "raw_id": str(raw_id),
                    "payload_hash": payload_hash,
                }
            ),
            status_code=200,
            headers=_build_headers(),
            mimetype="application/json",
        )
    except ValueError as exc:
        logging.exception("Asset ingest validation failed")
        return _bad_request(str(exc))
    except Exception:
        logging.exception("Asset ingest failed")
        return _internal_error()
