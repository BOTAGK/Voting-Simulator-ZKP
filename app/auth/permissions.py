from fastapi import HTTPException, Request, status

from app.auth.session import is_admin_authenticated
from app.core.config import get_settings


def require_admin(request: Request) -> str:
    if not is_admin_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )

    return get_settings().admin_username