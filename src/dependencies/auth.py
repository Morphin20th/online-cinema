from typing import Optional

from fastapi import Request, HTTPException, status, Depends
from redis import Redis
from sqlalchemy.orm import Session

from src.config import Settings, get_settings
from src.database import UserModel, get_db
from src.dependencies.config import get_redis_client
from src.security.interfaces import JWTAuthInterface
from src.security.token_manager import JWTManager


def get_jwt_auth_manager(
    settings: Settings = Depends(get_settings),
) -> JWTAuthInterface:
    """
    Dependency that provides an instance of the JWT authentication manager.

    Args:
        settings (Settings): Application settings with secret keys and algorithm.

    Returns:
        JWTAuthInterface: Instance of a class implementing JWT operations.
    """
    return JWTManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.ALGORITHM,
    )


def get_token(request: Request) -> str:
    """
    Extracts the Bearer token from the Authorization header in the request.

    Args:
        request (Request): The current FastAPI request.

    Returns:
        str: The JWT access token.
    """
    authorization: Optional[str] = request.headers.get("Authorization")

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
    jwt_manager: JWTAuthInterface = Depends(get_jwt_auth_manager),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> UserModel:
    """
    Dependency that retrieves the currently authenticated user from the token.

    Verifies the token, checks for blacklisting, and fetches the user from the database.

    Args:
        token (str): JWT access token from the Authorization header.
        jwt_manager (JWTAuthInterface): JWT token decoding logic.
        db (Session): SQLAlchemy database session.
        redis (Redis): Redis instance used for token blacklisting.

    Returns:
        UserModel: The currently authenticated and active user.
    """
    if redis.get(f"bl:{token}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been blacklisted",
        )

    try:
        payload = jwt_manager.decode_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload.",
            )

        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user.",
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )
