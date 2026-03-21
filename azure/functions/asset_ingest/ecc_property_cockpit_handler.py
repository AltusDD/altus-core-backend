from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from ecc_property_cockpit_service import build_property_cockpit

_HANDLER_NAME = "ecc-property-cockpit"
_DOMAIN_SIGNATURE = "ecc.property.cockpit.v1"


def handle_ecc_property_cockpit(
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

    deal_id = (req.params.get("dealId") or "").strip() or None
    transaction_id = (req.params.get("transactionId") or "").strip() or None

    try:
        return _json_response(build_property_cockpit(asset_id, deal_id, transaction_id), 200, build_headers)
    except Exception:
        logging.exception("ECC property cockpit failed")
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
