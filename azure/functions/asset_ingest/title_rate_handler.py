from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from title_rate_provider import TitleRateProviderError, quote_title_rate


def handle_title_rate_quote(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    try:
        payload = req.get_json()
    except ValueError:
        return _error_response("VALIDATION_FAILED", "Request body must be valid JSON", 400, build_headers)

    if not isinstance(payload, dict):
        return _error_response("VALIDATION_FAILED", "Request body must be an object", 400, build_headers)

    try:
        result = quote_title_rate(payload)
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            headers=build_headers(),
            mimetype="application/json",
        )
    except TitleRateProviderError as exc:
        status_code = _status_code_for_error(exc.code)
        return _error_response(exc.code, exc.message, status_code, build_headers, exc.details)
    except Exception:
        logging.exception("Title rate quote failed")
        return _error_response("INTERNAL_ERROR", "Internal server error", 500, build_headers)


def _status_code_for_error(code: str) -> int:
    if code == "VALIDATION_FAILED":
        return 400
    if code in {"TITLE_RATE_PROVIDER_NOT_CONFIGURED", "UNSUPPORTED_TITLE_RATE_PROVIDER"}:
        return 501
    return 500


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
