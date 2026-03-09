from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from ecc_portfolio_summary_service import build_portfolio_summary

_HANDLER_NAME = "ecc-portfolio-summary"
_DOMAIN_SIGNATURE = "ecc.portfolio.summary.v1"


def handle_ecc_portfolio_summary(
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
        payload = {"data": build_portfolio_summary(portfolio_id, req.params.get("asOfDate"))}
        return _json_response(payload, 200, build_headers)
    except Exception:
        logging.exception("ECC portfolio summary failed")
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
