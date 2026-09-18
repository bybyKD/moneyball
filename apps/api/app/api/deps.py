"""API dependencies: auth + session injection (spec §26)."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.errors import UnauthorizedError
from apps.api.app.core.security import decode_access_token
from apps.api.app.db.models.auth import User
from apps.api.app.db.session import get_session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_bearer = HTTPBearer(auto_error=False)


def _token_from_cookie(request: Request) -> str | None:
    return request.cookies.get(settings.auth_cookie_name)


async def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials if credentials else _token_from_cookie(request)
    if not token:
        raise UnauthorizedError("Authentication required")

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("uid") or 0)
    except Exception as exc:  # jwt.PyJWTError / malformed payload
        raise UnauthorizedError("Invalid or expired session") from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Account not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(current_user)]