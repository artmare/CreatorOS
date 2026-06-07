from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import get_settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str
    role: str = "owner"
    workspace_id: str = "ws_creatoros_demo"


async def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    """Validate Supabase JWTs when configured, otherwise keep local demo auth."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        settings = get_settings()
        if settings.supabase_jwt_secret:
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience=settings.supabase_jwt_audience,
                    options={"verify_aud": bool(settings.supabase_jwt_audience)},
                )
            except JWTError as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Supabase session",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc

            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user subject")

            app_metadata = payload.get("app_metadata") or {}
            email = payload.get("email") or "supabase-user@creatoros.local"
            admin_emails = {email.strip().lower() for email in settings.admin_email_allowlist.split(",") if email.strip()}
            role = "owner" if email.lower() in admin_emails else app_metadata.get("role", "member")
            workspace_id = app_metadata.get("workspace_id", "workspace_from_supabase")
            return CurrentUser(id=user_id, email=email, role=role, workspace_id=workspace_id)

        token_tail = token[-8:]
        return CurrentUser(id=f"user_{token_tail}", email="supabase-user@creatoros.local", role="member")
    return CurrentUser(id="user_artem", email="artem@example.com")


def require_admin(user: CurrentUser) -> CurrentUser:
    if user.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def get_admin_user(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return require_admin(user)
