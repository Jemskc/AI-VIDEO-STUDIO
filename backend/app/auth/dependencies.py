"""
Canonical auth dependency import path.

Wraps the existing JWT machinery in app.core.middleware.auth so routers
have a single, stable place to import authentication from.
"""
from fastapi import Depends

from app.core.middleware.auth import JWTBearer, get_current_user as _resolve_user
from app.models.user import CurrentUser


def get_current_user(token_payload: dict = Depends(JWTBearer())) -> CurrentUser:
    """Resolve the authenticated user from a validated JWT payload."""
    return CurrentUser(**_resolve_user(token_payload))


def get_current_user_id(current_user: CurrentUser = Depends(get_current_user)) -> int:
    """Resolve the authenticated user's database id as an int (JWT 'sub' is a string)."""
    return int(current_user.user_id)
