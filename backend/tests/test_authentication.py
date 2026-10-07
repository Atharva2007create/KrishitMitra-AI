from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.settings import Settings
from app.security.cognito import AuthenticationError, CognitoJWTVerifier


def build_verifier() -> tuple[CognitoJWTVerifier, object]:
    settings = Settings(
        aws_region="ap-south-1",
        aws_cognito_user_pool_id="ap-south-1_test",
        aws_cognito_client_id="test-client",
    )
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = CognitoJWTVerifier(settings)
    verifier._jwks_client = SimpleNamespace(  # type: ignore[assignment]
        get_signing_key_from_jwt=lambda _: SimpleNamespace(key=private_key.public_key())
    )
    return verifier, private_key


def token(private_key: object, **overrides: object) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "sub": "subject-1",
        "iss": "https://cognito-idp.ap-south-1.amazonaws.com/ap-south-1_test",
        "aud": "test-client",
        "token_use": "id",
        "exp": now + timedelta(minutes=5),
        "iat": now,
        "cognito:groups": ["administrators"],
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})


async def test_valid_signed_cognito_token() -> None:
    verifier, key = build_verifier()
    claims = await verifier.verify(token(key))
    assert claims.subject == "subject-1"
    assert claims.groups == frozenset({"administrators"})


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
        {"aud": "wrong-client"},
        {"token_use": "refresh"},
    ],
)
async def test_invalid_cognito_token_is_rejected(overrides: dict[str, object]) -> None:
    verifier, key = build_verifier()
    with pytest.raises(AuthenticationError):
        await verifier.verify(token(key, **overrides))
