"""users API — /users/me (spec §26 auth)."""

from apps.api.app.api.deps import current_user
from apps.api.app.db.models.auth import User
from apps.api.app.schemas.user import UserOut
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(current_user)) -> User:
    return user
