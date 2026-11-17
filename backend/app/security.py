"""JWT token issue + validation.

Flow: POST /api/auth/login (username/password) -> signed JWT (expires in JWT_EXPIRE_MINUTES).
Every protected route depends on `require_user`, which validates the Bearer token's signature
and expiry. No token / bad token / expired token -> 401 in the standard error envelope.
"""
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings
from .errors import AuthError

bearer_scheme = HTTPBearer(auto_error=False)


def verify_credentials(username: str, password: str, settings: Settings) -> bool:
    # compare_digest avoids timing attacks. A real system would check a hashed password in a DB.
    return hmac.compare_digest(username, settings.demo_username) and hmac.compare_digest(
        password, settings.demo_password
    )


def create_access_token(subject: str, settings: Settings) -> tuple[str, int]:
    expires_in = settings.jwt_expire_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(seconds=expires_in), "scope": "extract"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_in


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError("Missing bearer token")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired, please log in again")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
    return payload["sub"]
