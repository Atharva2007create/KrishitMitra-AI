from typing import Any

import pytest

from app.integrations.embeddings.base import EmbeddingError
from app.integrations.embeddings.credentials import resolve_gemini_api_key


class _SecretsClient:
    def __init__(self, secret_string: str) -> None:
        self.secret_string = secret_string
        self.requested_secret_id: str | None = None

    def get_secret_value(self, *, SecretId: str) -> dict[str, str]:  # noqa: N803
        self.requested_secret_id = SecretId
        return {"SecretString": self.secret_string}


def _install_client(monkeypatch: pytest.MonkeyPatch, client: _SecretsClient) -> None:
    def fake_client(service_name: str, **kwargs: Any) -> _SecretsClient:
        assert service_name == "secretsmanager"
        assert kwargs["region_name"] == "ap-south-1"
        return client

    monkeypatch.setattr("app.integrations.embeddings.credentials.boto3.client", fake_client)


def test_explicit_key_takes_precedence_without_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    resolve_gemini_api_key.cache_clear()

    def unexpected_client(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Secrets Manager must not be called for an explicit key")

    monkeypatch.setattr("app.integrations.embeddings.credentials.boto3.client", unexpected_client)
    assert resolve_gemini_api_key(" local-key ", "arn:unused", "ap-south-1") == "local-key"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ('{"api_key":"json-key"}', "json-key"),
        ('{"GEMINI_API_KEY":"uppercase-key"}', "uppercase-key"),
        ("raw-key", "raw-key"),
    ],
)
def test_resolves_supported_secret_shapes(
    monkeypatch: pytest.MonkeyPatch, stored: str, expected: str
) -> None:
    resolve_gemini_api_key.cache_clear()
    client = _SecretsClient(stored)
    _install_client(monkeypatch, client)

    assert resolve_gemini_api_key("", "arn:gemini", "ap-south-1") == expected
    assert client.requested_secret_id == "arn:gemini"


def test_rejects_secret_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    resolve_gemini_api_key.cache_clear()
    _install_client(monkeypatch, _SecretsClient('{"wrong":"value"}'))

    with pytest.raises(EmbeddingError, match="does not contain api_key"):
        resolve_gemini_api_key("", "arn:gemini", "ap-south-1")
