import asyncio
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError
from jwt.types import Options

from app.core.settings import Settings


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True)
class CognitoClaims:
    subject: str
    token_use: str
    phone_number: str | None
    email: str | None
    groups: frozenset[str]


class CognitoJWTVerifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jwks_client = PyJWKClient(
            f"{settings.cognito_issuer}/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=settings.jwt_jwks_cache_seconds,
        )

    async def verify(self, token: str) -> CognitoClaims:
        if not self.settings.aws_cognito_user_pool_id or not self.settings.aws_cognito_client_id:
            raise AuthenticationError("Cognito authentication is not configured")
        try:
            signing_key = await asyncio.to_thread(self._jwks_client.get_signing_key_from_jwt, token)
            unverified = jwt.decode(token, options={"verify_signature": False})
            token_use = unverified.get("token_use")
            options: Options = {"require": ["exp", "iss", "sub", "token_use"]}
            audience = self.settings.aws_cognito_client_id if token_use == "id" else None
            if token_use == "access":
                options["verify_aud"] = False
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.settings.cognito_issuer,
                audience=audience,
                options=options,
            )
            if token_use not in {"id", "access"}:
                raise AuthenticationError("Unsupported Cognito token type")
            if (
                token_use == "access"
                and claims.get("client_id") != self.settings.aws_cognito_client_id
            ):
                raise AuthenticationError("Cognito client does not match")
            groups_value = claims.get("cognito:groups", [])
            groups = frozenset(groups_value if isinstance(groups_value, list) else [])
            return CognitoClaims(
                subject=str(claims["sub"]),
                token_use=str(token_use),
                phone_number=claims.get("phone_number"),
                email=claims.get("email"),
                groups=groups,
            )
        except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError("Invalid or expired authentication token") from exc
