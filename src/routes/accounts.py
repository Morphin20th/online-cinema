from datetime import datetime, timezone, timedelta
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from pydantic import EmailStr
from redis import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.config import Settings, get_settings
from src.database import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    RefreshTokenModel,
    PasswordResetTokenModel,
    CartModel,
    get_db,
)
from src.dependencies import (
    get_jwt_auth_manager,
    get_email_sender,
    get_redis_client,
    get_token,
    get_current_user,
)
from src.schemas import (
    BASE_AUTH_EXAMPLES,
    CURRENT_USER_EXAMPLES,
    INVALID_CREDENTIAL_EXAMPLES,
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    ChangePasswordRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    LogoutRequestSchema,
    EmailRequestSchema,
    TokenRefreshRequestSchema,
    TokenRefreshResponseSchema,
    MessageResponseSchema,
)
from src.security.interfaces import JWTAuthInterface
from src.services import EmailSenderInterface
from src.utils import generate_secure_token, aggregate_error_examples

router = APIRouter()


def get_user_by_email(email: str, db: Session) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email.ilike(f"%{email}%")).first()


@router.post(
    "/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email an password",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found", examples={"not_found": "Group not found."}
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={
                "email_conflict": "A user with this email test@example.com already exists."
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "An error occurred during user creation."},
        ),
    },
)
def create_user(
    user_data: UserRegistrationRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_email_sender),
    settings: Settings = Depends(get_settings),
) -> UserRegistrationResponseSchema:
    """Create a new user account and send an activation email.

    Args:
        user_data: Registration data containing email and password
        background_tasks: Background tasks handler
        db: DB session
        email_sender: Email service
        settings: App settings

    Returns:
        Created user data
    """
    existing_user = get_user_by_email(user_data.email, db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with this email {user_data.email} already exists.",
        )

    group = db.query(UserGroupModel).filter_by(name=UserGroupEnum.USER).first()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found."
        )

    try:
        new_user = UserModel.create(
            email=user_data.email,
            new_password=user_data.password,
            group_id=group.id,
        )
        activation_token = ActivationTokenModel.create(
            user_id=new_user.id,
            token=generate_secure_token(),
            days=settings.ACTIVATION_TOKEN_LIFE,
        )
        new_user.activation_token = activation_token

        new_cart = CartModel(user=new_user)

        db.add_all([new_user, activation_token, new_cart])
        db.flush()
        db.commit()

        db.refresh(activation_token)
        token_value = activation_token.token

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during user creation.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_activation_email,
            user_data.email,
            token_value,
        )
    return UserRegistrationResponseSchema.model_validate(new_user)


@router.post(
    "/resend-activation/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Resend User Activation Email",
    description="Endpoint for resending User Activation Email",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={
                "message": "A new activation link has been sent.",
                "activated": "User is already activated.",
            },
        ),
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={"token_valid": "Activation token still valid."},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "no_user_found": "User with given email test@example.com not found."
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "An error occurred while creating the token."},
        ),
    },
)
def resend_activation(
    user_data: EmailRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_email_sender),
    settings: Settings = Depends(get_settings),
) -> MessageResponseSchema:
    """Resend activation email for an unactivated user account.

    Args:
        user_data: User's email data
        background_tasks: Background tasks handler
        db: DB session
        email_sender: Email service
        settings: App settings

    Returns:
        Success message
    """
    existing_user = get_user_by_email(user_data.email, db)

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with given email {user_data.email} not found.",
        )

    if existing_user.is_active:
        return MessageResponseSchema(message="User is already activated.")

    existing_token = existing_user.activation_token

    if existing_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token still valid.",
        )

    try:
        activation_token = ActivationTokenModel.create(
            user_id=existing_user.id,
            token=generate_secure_token(),
            days=settings.ACTIVATION_TOKEN_LIFE,
        )
        db.add(activation_token)
        existing_user.activation_token = activation_token

        db.commit()

        db.refresh(activation_token)
        token_value = activation_token.token
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the token.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_activation_email,
            user_data.email,
            token_value,
        )
    return MessageResponseSchema(message="A new activation link has been sent.")


@router.get(
    "/activate/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User Activation",
    description="Activate user account by verifying the provided email and activation token.",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "User account activated successfully."},
        ),
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={"invalid": "Invalid or expired token"},
        ),
    },
)
def activate_account(
    background_tasks: BackgroundTasks,
    email: EmailStr = Query(...),
    token: str = Query(...),
    email_sender: EmailSenderInterface = Depends(get_email_sender),
    db: Session = Depends(get_db),
) -> MessageResponseSchema:
    """Activate user account using email and token.

    Args:
        background_tasks: Background tasks handler
        email: User's email
        token: Activation token
        email_sender: Email service
        db: DB session

    Returns:
        Success message
    """
    activation_token = (
        db.query(ActivationTokenModel)
        .join(UserModel)
        .filter(
            UserModel.email == email,
            ActivationTokenModel.token == token,
        )
        .first()
    )

    if not activation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )

    try:
        user = activation_token.user
        user.is_active = True
        db.delete(activation_token)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
    else:
        background_tasks.add_task(
            email_sender.send_activation_confirmation_email, email
        )

    return MessageResponseSchema(message="User account activated successfully.")


@router.post(
    "/login/",
    response_model=UserLoginResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Logs in a user by validating their credentials",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized",
            examples={"credentials": "Invalid email or password."},
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Your account is not activated."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "An error occurred while creating the token"},
        ),
    },
)
def login_user(
    user_data: UserLoginRequestSchema,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    jwt_manager: JWTAuthInterface = Depends(get_jwt_auth_manager),
) -> UserLoginResponseSchema:
    """Log in user and generate access and refresh tokens.

    Args:
        user_data: Login credentials
        db: DB session
        settings: App settings
        jwt_manager: JWT handler

    Returns:
        Access and refresh tokens
    """
    user: Optional[UserModel] = get_user_by_email(user_data.email, db)

    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not activated",
        )

    jwt_refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    try:
        db.query(RefreshTokenModel).filter_by(
            user_id=user.id
        ).delete()  # delete existing token

        new_refresh_token = RefreshTokenModel.create(
            user_id=user.id, token=jwt_refresh_token, days=settings.LOGIN_DAYS
        )
        db.add(new_refresh_token)
        db.flush()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the token.",
        )

    jwt_access_token = jwt_manager.create_access_token(data={"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token, refresh_token=jwt_refresh_token
    )


@router.post(
    "/logout/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="User Logout",
    description="Endpoint for user logout",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Logged out successfully."},
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=BASE_AUTH_EXAMPLES
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Failed to logout. Try again."},
        ),
    },
)
def logout_user(
    user_data: LogoutRequestSchema,
    db: Session = Depends(get_db),
    token: str = Depends(get_token),
    jwt_manager: JWTAuthInterface = Depends(get_jwt_auth_manager),
    redis: Redis = Depends(get_redis_client),
) -> MessageResponseSchema:
    """Log out user by invalidating refresh and access tokens.

    Args:
        user_data: Logout request data
        db: DB session
        token: Access token
        jwt_manager: JWT handler
        redis: Redis client

    Returns:
        Success message
    """
    try:
        payload = jwt_manager.decode_token(token)
    except HTTPException:
        raise

    token_record = (
        db.query(RefreshTokenModel).filter_by(token=user_data.refresh_token).first()
    )
    if token_record:
        try:
            db.delete(token_record)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout. Try again.",
            )

    # Add access token to blacklist (Redis) with TTL
    exp = payload.get("exp")
    if exp:
        ttl = exp - int(datetime.now(timezone.utc).timestamp())
        redis.setex(f"bl:{token}", ttl, "blacklisted")

    return MessageResponseSchema(message="Logged out successfully.")


@router.post(
    "/refresh/",
    response_model=TokenRefreshResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Refreshes the access token using a valid refresh token",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden", examples={"inactive_user": "Inactive user."}
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={
                "refresh_missing": "Refresh token not found.",
            },
        ),
    },
)
def refresh_token(
    token_data: TokenRefreshRequestSchema,
    db: Session = Depends(get_db),
    jwt_manager: JWTAuthInterface = Depends(get_jwt_auth_manager),
    current_user: UserModel = Depends(get_current_user),
) -> TokenRefreshResponseSchema:
    """
    Refreshes the access token using a valid refresh token.

    Args:
        token_data (TokenRefreshRequestSchema): An instance containing the
            refresh token to be validated.
        db (Session): The database session dependency used to query or modify
            database records.
        jwt_manager (JWTAuthInterface): The dependency responsible for handling
            JSON Web Token (JWT) operations, including token decoding and creation.
        current_user (UserModel): The currently authenticated user, resolved
            using the authentication mechanism.

    Returns:
        TokenRefreshResponseSchema: An instance containing the newly generated
        access token.
    """
    try:
        payload = jwt_manager.decode_token(token_data.refresh_token, is_refresh=True)
    except HTTPException:
        raise

    user_id = payload.get("user_id")
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not belong to the authenticated user.",
        )

    token_record = (
        db.query(RefreshTokenModel).filter_by(token=token_data.refresh_token).first()
    )
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found."
        )

    if token_record.expires_at < datetime.now(timezone.utc):
        db.delete(token_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired."
        )

    new_access_token = jwt_manager.create_access_token(
        data={"user_id": current_user.id}, expires_delta=timedelta(minutes=15)
    )

    return TokenRefreshResponseSchema(access_token=new_access_token)


@router.post(
    "/change-password/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Password Change for an authenticated user",
    description="Password Change",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Password has been changed successfully!"},
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=INVALID_CREDENTIAL_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden", examples={"inactive_user": "Inactive user."}
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={
                "password_conflict": "New password cannot be same as the old one."
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred during new password creation."
            },
        ),
    },
)
def change_password(
    user_data: ChangePasswordRequestSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> MessageResponseSchema:
    """
    Handles the password change process for an authenticated user.

    Args:
        user_data (ChangePasswordRequestSchema): A schema containing the user's old password
            and the new password to be set.
        db (Session): Database session used for committing changes.
        current_user (UserModel): The currently authenticated user.

    Returns:
        MessageResponseSchema: A message response schema indicating successful password
        change.
    """
    if not current_user.verify_password(user_data.old_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user_data.old_password == user_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New password cannot be same as the old one.",
        )

    try:
        current_user.password = user_data.new_password
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during new password creation.",
        )

    return MessageResponseSchema(message="Password has been changed successfully!")


@router.post(
    "/reset-password/request/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Password Reset Request",
    description="Handles the process of requesting a password reset",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={
                "message": "If you have an account, you will receive an email with instructions."
            },
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Something went wrong."},
        ),
    },
)
def reset_password_request(
    user_data: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_email_sender),
) -> MessageResponseSchema:
    """
    Handles the process of requesting a password reset.

    Args:
        user_data (PasswordResetRequestSchema): Contains the email for the user requesting the password reset.
        background_tasks (BackgroundTasks): Background tasks handler for asynchronous execution.
        db (Session): Dependency-injected database session for executing queries.
        email_sender (EmailSenderInterface): Dependency-injected email sender instance.

    Returns:
        MessageResponseSchema: Confirms that instructions for resetting the password have been sent to the
        provided email if it is associated with an active account.
    """
    user = get_user_by_email(user_data.email, db)

    if not user or not user.is_active:
        return MessageResponseSchema(
            message="If you have an account, you will receive an email with instructions."
        )

    try:
        db.query(PasswordResetTokenModel).filter_by(user_id=user.id).delete()
        reset_token = PasswordResetTokenModel(user_id=cast(int, user.id))
        db.add(reset_token)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_password_reset_email, user_data.email, reset_token.token
        )

    return MessageResponseSchema(
        message="If you have an account, you will receive an email with instructions."
    )


@router.post(
    "/reset-password/complete/",
    response_model=MessageResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Password Reset Completion",
    description="Handles the completion of a password reset process for a user.",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Your password has been successfully changed!"},
        ),
        status.HTTP_400_BAD_REQUEST: aggregate_error_examples(
            description="Bad Request",
            examples={"invalid_token_email": "Invalid email or token."},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"not_found": "Token not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={
                "internal_server": "Error occurred during new password creation."
            },
        ),
    },
)
def reset_password(
    user_data: PasswordResetCompleteRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSenderInterface = Depends(get_email_sender),
) -> MessageResponseSchema:
    """Complete password reset process using token and new password.

    Args:
        user_data: Password reset data
        background_tasks: Background tasks handler
        db: DB session
        email_sender: Email service

    Returns:
        Success message
    """
    user = get_user_by_email(user_data.email, db)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
        )

    token_record = db.query(PasswordResetTokenModel).filter_by(user_id=user.id).first()
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found."
        )

    expires_at = cast(datetime, token_record.expires_at).replace(tzinfo=timezone.utc)

    if (
        not token_record
        or token_record.token != user_data.token
        or expires_at < datetime.now(timezone.utc)
    ):
        if token_record:
            db.delete(token_record)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
        )

    try:
        user.password = user_data.password
        db.delete(token_record)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred during new password creation.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_password_reset_complete_email, user_data.email
        )

    return MessageResponseSchema(message="Your password has been successfully changed!")
