"""
Lightweight representation of the authenticated user derived from JWT claims.

Not an ORM model — app.core.middleware.auth.get_current_user returns a dict
of token claims ({"user_id": ..., "role": ...}), not a hydrated database row.
"""
from pydantic import BaseModel


class CurrentUser(BaseModel):
    user_id: str
    role: str = "user"
