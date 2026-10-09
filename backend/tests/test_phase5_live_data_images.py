import importlib.util
import io
import json
import os
import urllib.error
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from app.core.settings import Settings
from app.integrations.government.http import GovernmentSourceError, SafeGovernmentHttpClient
from app.integrations.government.imd import ImdWeatherAdapter
from app.integrations.government.market import AgmarknetMarketAdapter
from app.integrations.government.service import LiveAgricultureDataService


class FakeGovernmentClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    async def get_json(self, *_: object, **__: object) -> object:
        return self.payload


async def test_safe_government_client_rejects_unapproved_host() -> None:
    client = SafeGovernmentHttpClient({"api.imd.gov.in"}, 1, 1, 1000)
    with pytest.raises(GovernmentSourceError) as error:
        await client.get_json("https://127.0.0.1/internal")
    assert error.value.code == "UNAPPROVED_SOURCE_HOST"


async def test_imd_adapter_normalizes_official_observation() -> None:
    client = FakeGovernmentClient(
        [
            {
                "ID": "MUM",
                "STATE": "MAHARASHTRA",
                "DISTRICT": "PUNE",
                "STATION": "PUNE",
                "DATE": "2026-10-08",
                "TIME": "06:30:00",
                "CURR_TEMP": "28.5",
                "RH": "72",
                "RAINFALL": "3.2",
                "WIND_SPEED": "8",
            }
        ]
    )
    adapter = ImdWeatherAdapter(  # type: ignore[arg-type]
        client, "https://api.imd.gov.in/api/v1", "Authorization", "credential"
    )
    result = await adapter.observations("Maharashtra", "Pune")
    assert result[0].station_name == "PUNE"
    assert str(result[0].temperature_c) == "28.5"
    assert result[0].provenance.organization == "India Meteorological Department"
    assert result[0].provenance.data_timestamp == result[0].observed_at


async def test_market_adapter_normalizes_agmarknet_record() -> None:
    client = FakeGovernmentClient(
        {
            "records": [
                {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "market": "Pune",
                    "commodity": "Arhar (Tur/Red Gram)(Whole)",
                    "variety": "Other",
                    "arrival_date": "08/10/2026",
                    "min_price": "6500",
                    "max_price": "7100",
                    "modal_price": "6900",
                }
            ]
        }
    )
    adapter = AgmarknetMarketAdapter(  # type: ignore[arg-type]
        client, "https://api.data.gov.in/resource", "resource-id", "key"
    )
    result = await adapter.prices("Maharashtra", "Pune", None, "Arhar")
    assert result[0].market == "Pune"
    assert str(result[0].modal_price) == "6900"
    assert result[0].unit == "INR/quintal"


async def test_unconfigured_official_sources_fail_closed() -> None:
    service = LiveAgricultureDataService(Settings(app_env="test"))
    with pytest.raises(GovernmentSourceError) as weather_error:
        await service.weather("Maharashtra", "Pune")
    assert weather_error.value.code == "SOURCE_AUTHENTICATION_REQUIRED"
    with pytest.raises(GovernmentSourceError) as market_error:
        await service.market_prices("Maharashtra", "Pune")
    assert market_error.value.code == "SOURCE_AUTHENTICATION_REQUIRED"
    with pytest.raises(GovernmentSourceError) as regulatory_error:
        await service.validate_pesticide("unknown")
    assert regulatory_error.value.code == "REGULATORY_VALIDATION_UNAVAILABLE"


async def test_stale_weather_is_not_presented_as_current() -> None:
    stale_time = datetime.now(UTC) - timedelta(days=2)
    client = FakeGovernmentClient(
        [
            {
                "STATE": "MAHARASHTRA",
                "DISTRICT": "PUNE",
                "STATION": "PUNE",
                "DATE": stale_time.date().isoformat(),
                "TIME": stale_time.time().replace(microsecond=0).isoformat(),
            }
        ]
    )
    service = LiveAgricultureDataService(
        Settings(app_env="test", imd_api_auth_value="credential", weather_max_age_seconds=3600)
    )
    service.weather_adapter = ImdWeatherAdapter(  # type: ignore[arg-type]
        client, "https://api.imd.gov.in/api/v1", "Authorization", "credential"
    )
    with pytest.raises(GovernmentSourceError) as error:
        await service.weather("Maharashtra", "Pune")
    assert error.value.code == "STALE_LIVE_DATA"


async def test_market_results_are_sorted_by_actual_arrival_date() -> None:
    client = FakeGovernmentClient(
        {
            "records": [
                {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "market": "Pune",
                    "commodity": "Arhar",
                    "arrival_date": "01/10/2026",
                    "modal_price": "6000",
                },
                {
                    "state": "Maharashtra",
                    "district": "Pune",
                    "market": "Pune",
                    "commodity": "Arhar",
                    "arrival_date": "08/10/2026",
                    "modal_price": "6500",
                },
            ]
        }
    )
    service = LiveAgricultureDataService(Settings(app_env="test", data_gov_api_key="credential"))
    service.market_adapter = AgmarknetMarketAdapter(  # type: ignore[arg-type]
        client, "https://api.data.gov.in/resource", "resource-id", "credential"
    )
    result = await service.market_prices("Maharashtra", "Pune", commodity="Arhar")
    assert result[0].arrival_date.date().isoformat() == "2026-10-08"


def test_source_matrix_does_not_claim_unavailable_integrations_are_live() -> None:
    service = LiveAgricultureDataService(Settings(app_env="test"))
    statuses = {item.code: item.status for item in service.capabilities()}
    assert statuses == {
        "IMD": "BLOCKED",
        "AGMARKNET": "BLOCKED",
        "ENAM": "PARTIAL",
        "PPQS_CIBRC": "PARTIAL",
        "MAHARASHTRA_AGRICULTURE": "PARTIAL",
        "SOIL_HEALTH_CARD": "BLOCKED",
    }


def _load_lambda() -> Any:
    configured = os.environ.get("PHASE5_LAMBDA_HANDLER_PATH")
    path = (
        Path(configured)
        if configured
        else Path(__file__).parents[2]
        / "infrastructure"
        / "lambda"
        / "image_foundation"
        / "handler.py"
    )
    spec = importlib.util.spec_from_file_location("phase5_image_handler", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lambda_rejects_untrusted_s3_event() -> None:
    handler = _load_lambda()
    with pytest.raises(handler.ImagePipelineError) as error:
        handler._event_object(
            {"Records": [{"s3": {"bucket": {"name": "bucket"}, "object": {"key": "x"}}}]}
        )
    assert error.value.code == "INVALID_OBJECT_KEY"


def test_lambda_validates_image_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _load_lambda()

    class S3:
        def head_object(self, **_: object) -> dict[str, object]:
            return {
                "ContentLength": 8,
                "ContentType": "image/png",
                "Metadata": {
                    "attachment-id": "a",
                    "user-id": "u",
                    "session-id": "s",
                    "source-type": "UPLOAD",
                },
            }

        def get_object(self, **_: object) -> dict[str, object]:
            return {"Body": io.BytesIO(b"notimage")}

    monkeypatch.setattr(handler.boto3, "client", lambda *args, **kwargs: S3())
    with pytest.raises(handler.ImagePipelineError) as error:
        handler._validate_and_load("bucket", "farmer-uploads/u/s/a/image.png")
    assert error.value.code == "IMAGE_SIGNATURE_INVALID"


def test_lambda_rejects_treatment_content_from_visual_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = _load_lambda()
    model_result = {
        "image_sufficient": True,
        "quality": {"focus": "GOOD", "lighting": "GOOD", "crop_visible": True, "notes": []},
        "observations": [{"feature": "spots", "location": "leaf", "severity": "LOW"}],
        "candidate_issues": [
            {"name": "candidate", "confidence": "LOW", "reason": "apply a treatment"}
        ],
        "follow_up_questions": [],
    }
    envelope = {"candidates": [{"content": {"parts": [{"text": json.dumps(model_result)}]}}]}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int) -> bytes:
            return json.dumps(envelope).encode()

    monkeypatch.setattr(handler, "_gemini_key", lambda: "secret")
    monkeypatch.setattr(handler.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(handler.ImagePipelineError) as error:
        handler._analyze(b"image", "image/jpeg")
    assert error.value.code == "MODEL_SAFETY_REJECTED"


def test_lambda_retries_transient_model_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _load_lambda()
    model_result = {
        "image_sufficient": False,
        "quality": {"focus": "POOR", "lighting": "GOOD", "crop_visible": False, "notes": []},
        "observations": [],
        "candidate_issues": [],
        "follow_up_questions": ["Upload a clearer crop image."],
    }
    envelope = {"candidates": [{"content": {"parts": [{"text": json.dumps(model_result)}]}}]}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self, _: int) -> bytes:
            return json.dumps(envelope).encode()

    calls = 0

    def urlopen(*_: object, **__: object) -> Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise urllib.error.URLError("temporary")
        return Response()

    monkeypatch.setattr(handler, "_gemini_key", lambda: "secret")
    monkeypatch.setattr(handler.time, "sleep", lambda _: None)
    monkeypatch.setattr(handler.urllib.request, "urlopen", urlopen)
    assert handler._analyze(b"image", "image/jpeg")["image_sufficient"] is False
    assert calls == 2


def test_image_result_keys_are_attachment_scoped_and_hash_idempotent() -> None:
    handler = _load_lambda()
    key = "farmer-uploads/user/session/attachment/leaf.jpg"
    assert handler._result_key(key) == "analysis-results/attachment.json"
    assert handler._hash_key("abc") == handler._hash_key("abc")
    assert datetime.now(UTC).tzinfo is not None
