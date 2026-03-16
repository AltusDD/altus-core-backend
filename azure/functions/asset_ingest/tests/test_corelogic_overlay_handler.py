import json
import pathlib
import sys
import types
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

try:
    import corelogic_overlay_handler
except ModuleNotFoundError as exc:
    if exc.name != "azure":
        raise

    azure_module = types.ModuleType("azure")
    functions_module = types.ModuleType("azure.functions")
    azure_module.functions = functions_module
    sys.modules["azure"] = azure_module
    sys.modules["azure.functions"] = functions_module
    import corelogic_overlay_handler


class CoreLogicOverlayHandlerTests(unittest.TestCase):
    def test_handler_returns_mock_overlay_payload(self) -> None:
        fake_request = _FakeHttpRequest(
            params={"address": "1518 Summit Ridge Dr, Kansas City, MO"},
            headers={"x-altus-operator": "tester"},
        )

        original_func = corelogic_overlay_handler.func
        corelogic_overlay_handler.func = SimpleNamespace(HttpResponse=_FakeHttpResponse)
        try:
            response = corelogic_overlay_handler.handle_corelogic_overlay(
                fake_request,
                lambda: {"x-altus-build-sha": "test"},
            )
        finally:
            corelogic_overlay_handler.func = original_func

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.get_body().decode("utf-8"))
        self.assertEqual(payload["subject"]["address"], "1518 Summit Ridge Dr, Kansas City, MO")
        self.assertEqual(payload["subject"]["lat"], 39.0997)
        self.assertEqual(payload["overlays"]["corelogicLayerStatus"], "mock_ready")
        self.assertTrue(payload["meta"]["mock"])


class _FakeHttpRequest:
    def __init__(self, params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> None:
        self.params = params or {}
        self.headers = headers or {}


class _FakeHttpResponse:
    def __init__(self, body: str, status_code: int, headers: dict | None = None, mimetype: str | None = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self.mimetype = mimetype
        self._body = body.encode("utf-8")

    def get_body(self) -> bytes:
        return self._body


if __name__ == "__main__":
    unittest.main()
