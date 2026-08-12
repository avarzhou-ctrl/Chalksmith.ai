import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from backend.app.core.config import Settings
from backend.app.core.errors import AppError

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    uid: str
    email: str | None = None


@lru_cache(maxsize=8)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(
        jwks_url,
        cache_jwk_set=True,
        lifespan=300,
        cache_keys=True,
        timeout=5,
    )


def _decode_clerk_token(token: str, settings: Settings) -> dict[str, Any]:
    if not settings.clerk_issuer:
        raise RuntimeError("CLERK_ISSUER is not configured.")

    jwks_url = settings.clerk_jwks_url or f"{settings.clerk_issuer}/.well-known/jwks.json"
    signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
    decode_options = {"require": ["exp", "sub"], "verify_aud": bool(settings.clerk_audience)}
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=settings.clerk_issuer,
        audience=settings.clerk_audience,
        options=decode_options,
        leeway=5,
    )

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidTokenError("The token has no valid subject.")
    authorized_party = claims.get("azp")
    if authorized_party and authorized_party not in settings.clerk_authorized_parties:
        raise InvalidTokenError("The token authorized party is not allowed.")
    return claims


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="authentication_required",
            message="A valid Clerk session token is required.",
            status_code=401,
        )

    try:
        claims = await asyncio.to_thread(
            _decode_clerk_token,
            credentials.credentials,
            request.app.state.settings,
        )
    except (PyJWKClientConnectionError, OSError, RuntimeError) as error:
        raise AppError(
            code="authentication_service_unavailable",
            message="The login session could not be verified.",
            status_code=503,
        ) from error
    except (InvalidTokenError, PyJWKClientError) as error:
        raise AppError(
            code="invalid_session_token",
            message="The login session is invalid or expired.",
            status_code=401,
        ) from error

    return AuthUser(uid=str(claims["sub"]), email=claims.get("email"))
