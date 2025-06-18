from fastapi import Depends, HTTPException
from starlette import status

from src.database import UserModel, UserGroupEnum
from src.dependencies.auth import get_current_user


def admin_required(current_user: UserModel = Depends(get_current_user)):
    if not current_user.group_id == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


def moderator_or_admin_required(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.group.name not in (UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Moderator or admin required.",
        )
    return current_user
