"""users API — /users/me (spec §26 auth)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from apps.api.app.db.models.auth import User
from apps.api.app.schemas.user import UserOut
from apps.api.app.api.deps import current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(current_user)) -> User:
    return user