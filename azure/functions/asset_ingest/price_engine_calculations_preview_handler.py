from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from price_engine_calculations import PriceEngineError
from price_engine_service import calculate_price_engine


def handle_price_engine_calculations_preview(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    payload = dict(req.params)

    try:
        result = calculate_price_engine(payload)
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            headers=build_headers(),
            mimetype="application/json",
        )
    except PriceEngineError as exc:
        status_code = 400 if exc.code != "INTERNAL_ERROR" else 500
        return _error_response(exc.code, exc.message, status_code, build_headers, exc.details)
    except Exception:
        logging.exception("Price engine calculations preview failed")
        return _error_response("INTERNAL_ERROR", "Internal server error", 500, build_headers)


def _error_response(
    code: str,
    message: str,
    status_code: int,
    build_headers: Callable[[], dict[str, str]],
    details: dict[str, object] | None = None,
) -> func.HttpResponse:
    payload = {"error": {"code": code, "message": message, "details": details or None}}
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        headers=build_headers(),
        mimetype="application/json",
    )
