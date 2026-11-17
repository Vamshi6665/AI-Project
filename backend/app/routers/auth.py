import logging

from fastapi import APIRouter, Depends

from ..config import Settings, get_settings
from ..errors import AuthError
from ..schemas import LoginRequest, TokenResponse
from ..security import create_access_token, require_user, verify_credentials
from .common import ok

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")


@router.post("/login")
def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
    if not verify_credentials(body.username, body.password, settings):
        logger.warning("login_failed", extra={"username": body.username})
        raise AuthError("Invalid username or password")
    token, expires_in = create_access_token(body.username, settings)
    logger.info("login_ok", extra={"username": body.username})
    return ok(TokenResponse(access_token=token, expires_in=expires_in))


@router.get("/me")
def me(user: str = Depends(require_user)):
    return ok({"username": user})
