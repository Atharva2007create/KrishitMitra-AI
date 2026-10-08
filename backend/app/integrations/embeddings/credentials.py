import json
from functools import lru_cache
from typing import cast

import boto3  # type: ignore[import-untyped]

from app.integrations.embeddings.base import EmbeddingError


@lru_cache(maxsize=4)
def resolve_gemini_api_key(api_key: str, secret_arn: str, region: str) -> str:
    """Resolve the embedding credential without logging or persisting its value."""
    if api_key.strip():
        return api_key.strip()
    if not secret_arn.strip():
        return ""

    try:
        response = boto3.client("secretsmanager", region_name=region).get_secret_value(
            SecretId=secret_arn
        )
        raw_secret = response.get("SecretString", "")
        secret_string = raw_secret if isinstance(raw_secret, str) else ""
        if not secret_string:
            raise EmbeddingError("Gemini secret has no SecretString value")
        try:
            parsed: object = json.loads(secret_string)
        except json.JSONDecodeError:
            resolved = secret_string
        else:
            if not isinstance(parsed, dict):
                raise EmbeddingError("Gemini secret must be a string or JSON object")
            parsed_mapping = cast(dict[str, object], parsed)
            secret_value = parsed_mapping.get("api_key") or parsed_mapping.get("GEMINI_API_KEY")
            resolved = secret_value if isinstance(secret_value, str) else ""
        if not resolved.strip():
            raise EmbeddingError("Gemini secret does not contain api_key")
        return resolved.strip()
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError("Unable to load Gemini credential from Secrets Manager") from exc
