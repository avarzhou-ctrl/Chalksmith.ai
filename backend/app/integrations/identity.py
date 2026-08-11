import asyncio
from dataclasses import dataclass

import firebase_admin
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

from backend.app.core.errors import AppError

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    uid: str
    email: str | None = None


def _ensure_firebase_app(project_id: str | None) -> None:
    try:
        firebase_admin.get_app()
    except ValueError:
        options = {"projectId": project_id} if project_id else None
        firebase_admin.initialize_app(options=options)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(
            code="authentication_required",
            message="A valid Identity Platform ID token is required.",
            status_code=401,
        )

    settings = request.app.state.settings
    _ensure_firebase_app(settings.identity_platform_project_id)
    try:
        claims = await asyncio.to_thread(auth.verify_id_token, credentials.credentials)
    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as error:
        raise AppError(
            code="invalid_identity_token",
            message="The login session is invalid or expired.",
            status_code=401,
        ) from error
    except Exception as error:
        raise AppError(
            code="identity_verification_failed",
            message="The login session could not be verified.",
            status_code=503,
        ) from error

    uid = claims.get("uid") or claims.get("sub")
    if not uid:
        raise AppError(
            code="invalid_identity_token",
            message="The login session has no user identifier.",
            status_code=401,
        )
    return AuthUser(uid=str(uid), email=claims.get("email"))
