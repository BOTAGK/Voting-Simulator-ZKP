from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.permissions import require_admin
from app.auth.session import (
    authenticate_admin,
    create_admin_session,
    delete_admin_session,
    get_admin_from_session,
    is_admin_authenticated,
)
from app.schemas.auth import AdminLogin, AdminRead



router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

@router.post(
    "/login",
    response_model =  AdminRead, 
)
def login_admin(
    data: AdminLogin,
    request: Request,
) -> AdminRead:
    current_admin = get_admin_from_session(request)
    
    if current_admin is not None and is_admin_authenticated(request):
        return AdminRead(username=current_admin)
    
    if not authenticate_admin(data.username, data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    
    create_admin_session(request, data.username)

    return AdminRead(username=data.username)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_admin(
    request: Request,
    _admin_username: str = Depends(require_admin),
) -> Response:
    delete_admin_session(request)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=AdminRead,
)
def get_current_admin(
    admin_username: str = Depends(require_admin),
) -> AdminRead:
    return AdminRead(username=admin_username)