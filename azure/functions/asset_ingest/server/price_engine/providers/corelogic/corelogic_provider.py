from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from server.price_engine.providers.corelogic.corelogic_client import CoreLogicClient
from server.price_engine.providers.corelogic.corelogic_config import load_corelogic_config
from server.price_engine.providers.corelogic.corelogic_models import mock_overlay_payload


@dataclass(frozen=True)
class CoreLogicProviderResponse:
    provider: str
    mode: str
    property_intelligence: dict[str, Any]


class CoreLogicProvider:
    provider_name = "corelogic"

    def __init__(self) -> None:
        self._config = load_corelogic_config()
        self._client = CoreLogicClient(self._config)

    def get_property_intelligence(self, *, property_address: str, operator: str = "system") -> CoreLogicProviderResponse:
        request = self._client.build_request(property_address=property_address, operator=operator)
        payload = self._client.fetch_property_intelligence(request)
        return CoreLogicProviderResponse(
            provider=self.provider_name,
            mode=str(payload["mode"]),
            property_intelligence=dict(payload["data"]),
        )

    def get_property_overlay_payload(self, *, property_address: str, operator: str = "system") -> dict[str, Any]:
        request = self._client.build_request(property_address=property_address, operator=operator)
        self._client._log_request(request)
        return mock_overlay_payload(property_address=property_address).to_dict()
