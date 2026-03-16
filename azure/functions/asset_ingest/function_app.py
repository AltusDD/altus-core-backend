import hashlib
import json
import logging
import os
import uuid
from typing import Any

import azure.functions as func
import requests
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from ecc_portfolio_summary_handler import handle_ecc_portfolio_summary
from ecc_portfolio_assets_handler import handle_ecc_portfolio_assets
from ecc_asset_search_handler import handle_ecc_asset_search
from ecc_asset_metrics_handler import handle_ecc_asset_metrics
from ecc_system_health_handler import handle_ecc_system_health
from corelogic_overlay_handler import handle_corelogic_overlay
from price_engine_handler import handle_price_engine_calculate
from title_rate_handler import handle_title_rate_quote

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

_ALLOWED_SOURCES = {"CORELOGIC", "MLS", "DOORLOOP", "MANUAL", "OTHER"}


class RuntimeConfig:
    def __init__(self) -> None:
        vault_url = os.getenv("KEY_VAULT_URL", "https://altus-core-staging-kv.vault.azure.net/")
        credential = ManagedIdentityCredential()
        self._secret_client = SecretClient(vault_url=vault_url, credential=credential)

        supabase_url_secret_name = os.getenv("SUPABASE_URL_SECRET_NAME", "SUPABASE_URL")
        supabase_key_secret_name = os.getenv("SUPABASE_SERVICE_ROLE_KEY_SECRET_NAME", "SUPABASE_SERVICE_ROLE_KEY")

        self.supabase_url = self._secret_client.get_secret(supabase_url_secret_name).value.rstrip("/")
        self.supabase_service_role_key = self._secret_client.get_secret(supabase_key_secret_name).value


_config: RuntimeConfig | None = None


def _build_headers() -> dict[str, str]:
    build_sha = os.getenv("ALTUS_BUILD_SHA", "unknown")
    return {
        "x-altus-build-sha": build_sha,
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


def _bad_request(message: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"ok": False, "error": message}),
        status_code=400,
        mimetype="application/json",
    )


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

        body = req.get_json()
        if not isinstance(body, dict):
            return _bad_request("Request body must be a JSON object")

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

        config = _get_config()

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

        asset_id = asset_row.get("id")
        if not asset_id:
            raise RuntimeError("assets insert did not return id")

        raw_row = _insert_supabase_row(
            table="asset_data_raw",
            payload={
                "organization_id": organization_id,
                "asset_id": asset_id,
                "source": source,
                "payload": raw_payload,
                "payload_sha256": payload_hash,
                "source_record_id": None,
            },
            config=config,
        )

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
            mimetype="application/json",
        )
    except ValueError as exc:
        return _bad_request(str(exc))
    except Exception:
        logging.exception("Asset ingest failed")
        return func.HttpResponse(
            json.dumps({"ok": False, "error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="ecc/portfolio/summary", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ecc_portfolio_summary(req: func.HttpRequest) -> func.HttpResponse:
    return handle_ecc_portfolio_summary(req, _build_headers)


@app.route(route="ecc/portfolio/assets", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ecc_portfolio_assets(req: func.HttpRequest) -> func.HttpResponse:
    return handle_ecc_portfolio_assets(req, _build_headers)


@app.route(route="ecc/assets/search", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ecc_asset_search(req: func.HttpRequest) -> func.HttpResponse:
    return handle_ecc_asset_search(req, _build_headers)


@app.route(route="ecc/assets/metrics", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ecc_asset_metrics(req: func.HttpRequest) -> func.HttpResponse:
    return handle_ecc_asset_metrics(req, _build_headers)


@app.route(route="ecc/system/health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ecc_system_health(req: func.HttpRequest) -> func.HttpResponse:
    return handle_ecc_system_health(req, _build_headers)


@app.route(route="price-engine/calculate", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def price_engine_calculate(req: func.HttpRequest) -> func.HttpResponse:
    return handle_price_engine_calculate(req, _build_headers)


@app.route(route="price-engine/title-rate-quote", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def price_engine_title_rate_quote(req: func.HttpRequest) -> func.HttpResponse:
    return handle_title_rate_quote(req, _build_headers)


@app.route(route="price-engine/corelogic-overlay", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def price_engine_corelogic_overlay(req: func.HttpRequest) -> func.HttpResponse:
    return handle_corelogic_overlay(req, _build_headers)
