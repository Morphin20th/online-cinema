from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from config import get_jwt_auth_manager
from database import UserModel
from database.session import get_db
from security.token_manager import JWTManager


def get_token(request: Request) -> str:
    authorization: str = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )

    return token


def get_current_user(
    token: str = Depends(get_token),
    jwt_manager: JWTManager = Depends(get_jwt_auth_manager),
    db: Session = Depends(get_db),
) -> type[UserModel]:
    try:
        payload = jwt_manager.decode_token(token)
        user_id = payload.get("user_id")
        print(payload.get("user_id"))

        if not user_id:
            print("no ID")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def check_admin_role(current_user: UserModel = Depends(get_current_active_user)):
    if not current_user.group_id == 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user
