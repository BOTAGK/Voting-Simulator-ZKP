from secrets import compare_digest

from fastapi import Request

from app.core.config import get_settings

ADMIN_SESSION_KEY = "admin_username"

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate an admin user based on the provided username and password."""
    settings = get_settings()
    
    username_matches = compare_digest(username, settings.admin_username)
    password_matches = compare_digest(password, settings.admin_password)

    return username_matches and password_matches

def create_admin_session(request: Request, username: str) -> None:
    request.session[ADMIN_SESSION_KEY] = username

def get_admin_from_session(request: Request) -> str | None:
    return request.session.get(ADMIN_SESSION_KEY)    

def is_admin_authenticated(request: Request) -> bool:
    username = get_admin_from_session(request)

    if username is None:
        return False
    
    return compare_digest(username, get_settings().admin_username)

def delete_admin_session(request: Request) -> None:
    request.session.pop(ADMIN_SESSION_KEY, None)