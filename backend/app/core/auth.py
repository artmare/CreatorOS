from dataclasses import dataclass

from fastapi import Header


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str = "owner"
    workspace_id: str = "ws_creatoros_demo"


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Development-safe auth boundary.

    Supabase JWT validation is wired here later; until configured, local routes use
    a deterministic demo user so the platform can run without provider secrets.
    """
    if authorization and authorization.startswith("Bearer "):
        token_tail = authorization[-8:]
        return CurrentUser(id=f"user_{token_tail}", email="supabase-user@creatoros.local")
    return CurrentUser(id="user_artem", email="artem@example.com")


def require_admin(user: CurrentUser) -> CurrentUser:
    if user.role not in {"owner", "admin"}:
        raise PermissionError("Admin access required")
    return user
