from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from ecc_asset_metrics_service import build_asset_metrics

_HANDLER_NAME = "ecc-asset-metrics"
_DOMAIN_SIGNATURE = "ecc.asset.metrics.v1"


def handle_ecc_asset_metrics(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    asset_id = (req.params.get("assetId") or "").strip()
    if not asset_id:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "assetId is required"}},
            400,
            build_headers,
        )

    try:
        window_days = int(req.params.get("windowDays", "30"))
    except ValueError:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "windowDays must be an integer"}},
            400,
            build_headers,
        )

    if window_days < 1 or window_days > 365:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "windowDays must be 1..365"}},
            400,
            build_headers,
        )

    try:
        return _json_response({"data": build_asset_metrics(asset_id, window_days)}, 200, build_headers)
    except Exception:
        logging.exception("ECC asset metrics failed")
        return _json_response(
            {"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
            500,
            build_headers,
        )


def _json_response(
    payload: dict[str, object],
    status_code: int,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    headers = build_headers()
    headers["x-ecc-handler"] = _HANDLER_NAME
    headers["x-ecc-domain-signature"] = _DOMAIN_SIGNATURE
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        headers=headers,
        mimetype="application/json",
    )
