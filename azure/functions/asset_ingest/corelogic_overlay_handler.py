from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from server.price_engine.providers.corelogic.corelogic_provider import CoreLogicProvider

_DEFAULT_ADDRESS = "1518 Summit Ridge Dr, Kansas City, MO"


def handle_corelogic_overlay(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    address = (req.params.get("address") or _DEFAULT_ADDRESS).strip()
    operator = (req.headers.get("x-altus-operator") or "system").strip() or "system"

    try:
        payload = CoreLogicProvider().get_property_overlay_payload(
            property_address=address,
            operator=operator,
        )
        return func.HttpResponse(
            json.dumps(payload),
            status_code=200,
            headers=build_headers(),
            mimetype="application/json",
        )
    except Exception:
        logging.exception("CoreLogic overlay payload failed")
        return func.HttpResponse(
            json.dumps(
                {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Internal server error",
                        "details": None,
                    }
                }
            ),
            status_code=500,
            headers=build_headers(),
            mimetype="application/json",
        )
