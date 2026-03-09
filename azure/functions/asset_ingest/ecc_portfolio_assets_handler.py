from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from ecc_portfolio_assets_service import build_portfolio_assets

_HANDLER_NAME = "ecc-portfolio-assets"
_DOMAIN_SIGNATURE = "ecc.portfolio.assets.v1"


def handle_ecc_portfolio_assets(
    req: func.HttpRequest,
    build_headers: Callable[[], dict[str, str]],
) -> func.HttpResponse:
    portfolio_id = (req.params.get("portfolioId") or "").strip()
    if not portfolio_id:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "portfolioId is required"}},
            400,
            build_headers,
        )

    try:
        limit = int(req.params.get("limit", "25"))
        offset = int(req.params.get("offset", "0"))
    except ValueError:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "limit and offset must be integers"}},
            400,
            build_headers,
        )

    if limit < 1 or limit > 100 or offset < 0:
        return _json_response(
            {"error": {"code": "VALIDATION_FAILED", "message": "limit must be 1..100 and offset must be >= 0"}},
            400,
            build_headers,
        )

    try:
        return _json_response(build_portfolio_assets(portfolio_id, limit, offset), 200, build_headers)
    except Exception:
        logging.exception("ECC portfolio assets failed")
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
