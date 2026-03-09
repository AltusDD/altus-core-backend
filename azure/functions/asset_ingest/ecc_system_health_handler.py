from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from ecc_system_health_service import build_system_health

_HANDLER_NAME = "ecc-system-health"
_DOMAIN_SIGNATURE = "ecc.system.health.v1"


def handle_ecc_system_health(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    try:
        return _json_response({"data": build_system_health()}, 200, build_headers)
    except Exception:
        logging.exception("ECC system health failed")
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
