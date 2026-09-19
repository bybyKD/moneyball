"""Auth routes — register / login / me (spec §26/§36)."""

from apps.api.app.core.config import settings
from apps.api.app.core.errors import ConflictError, ForbiddenError, UnauthorizedError
from apps.api.app.core.security import create_access_token, hash_password, verify_password
from apps.api.app.db.models import User  # noqa: F401  (registry side effect — keeps Alembic happy)
from apps.api.app.db.session import get_session
from apps.api.app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select

# schemas.auth already provides RegisterIn/LoginIn/TokenOut; keep this line
# intentionally absent so there is a single source of truth for auth schemas.

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: RegisterIn, response: Response, session=Depends(get_session)):
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise ConflictError("That email is already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), display_name=payload.display_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(str(user.id), user_id=user.id)
    response.set_cookie(
        settings.auth_cookie_name, token, httponly=True, samesite="lax", secure=settings.auth_cookie_secure, max_age=86400 * 7
    )
    return user


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, response: Response, session=Depends(get_session)):
    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise ForbiddenError("Account disabled")
    token = create_access_token(str(user.id), user_id=user.id)
    response.set_cookie(
        settings.auth_cookie_name, token, httponly=True, samesite="lax", secure=settings.auth_cookie_secure, max_age=86400 * 7
    )
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    response.delete_cookie(settings.auth_cookie_name)
    return None
