from __future__ import annotations

import json
import logging
from typing import Callable

import azure.functions as func

from adoption import PricingRequestContext, PricingScenario, resolve_pricing_gateway
from price_engine_service import PriceEngineError


def handle_price_engine_calculate(
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
        selection = resolve_pricing_gateway()
        scenario_id = str(payload.get("scenarioId") or payload.get("scenario_id") or "request")
        context = PricingRequestContext(
            correlation_id=req.headers.get("x-correlation-id", "price-engine-request"),
            organization_id=req.headers.get("x-organization-id"),
            actor_id=req.headers.get("x-actor-id"),
            trace_headers={
                key: value
                for key, value in req.headers.items()
                if key.lower().startswith("x-")
            },
        )
        result = selection.gateway.calculate(
            PricingScenario(
                scenario_id=scenario_id,
                inputs=payload,
                engine_version=selection.mode,
            ),
            context=context,
        )
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            headers=build_headers(),
            mimetype="application/json",
        )
    except PriceEngineError as exc:
        status_code = 400 if exc.code != "INTERNAL_ERROR" else 500
        return _error_response(exc.code, exc.message, status_code, build_headers, exc.details)
    except ValueError as exc:
        return _error_response("VALIDATION_FAILED", str(exc), 400, build_headers)
    except Exception:
        logging.exception("Price engine calculation failed")
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
