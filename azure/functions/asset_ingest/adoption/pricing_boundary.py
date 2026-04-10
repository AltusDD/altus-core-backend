from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from price_engine_service import calculate_price_engine


@dataclass(frozen=True)
class PricingRequestContext:
    correlation_id: str
    organization_id: str | None = None
    actor_id: str | None = None
    trace_headers: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PricingScenario:
    scenario_id: str
    inputs: Mapping[str, Any]
    engine_version: str | None = None


class PricingGateway(Protocol):
    def calculate(
        self,
        scenario: PricingScenario,
        *,
        context: PricingRequestContext,
    ) -> dict[str, Any]:
        ...


class LocalPriceEngineGateway:
    """Contract-preserving gateway backed by the in-repo price engine."""

    def calculate(
        self,
        scenario: PricingScenario,
        *,
        context: PricingRequestContext,
    ) -> dict[str, Any]:
        del context
        return calculate_price_engine(dict(scenario.inputs))


class RangeKeeperGatewayDeferred:
    """Placeholder until a bounded backend service adapter is approved."""

    def calculate(
        self,
        scenario: PricingScenario,
        *,
        context: PricingRequestContext,
    ) -> dict[str, Any]:
        del scenario
        del context
        raise NotImplementedError(
            "RangeKeeper remains deferred until a service-boundary adapter is approved for this backend."
        )
