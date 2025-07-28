from fastapi import Depends, HTTPException
from starlette import status

from src.database import UserModel, UserGroupEnum
from src.dependencies.auth import get_current_user


def admin_required(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    """
    Dependency that ensures the current user has admin privileges.

    Args:
        current_user (UserModel): The authenticated user retrieved via dependency.

    Returns:
        UserModel: The same user if they belong to the ADMIN group.
    """
    if current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required.",
        )
    return current_user


def moderator_or_admin_required(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """
    Dependency that allows access to moderators or administrators.

    Args:
        current_user (UserModel): The authenticated user retrieved via dependency.

    Returns:
        UserModel: The same user if they belong to the MODERATOR or ADMIN group.
    """
    if current_user.group.name not in (UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Moderator or admin required.",
        )
    return current_user
