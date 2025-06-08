import logging
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from config import get_jwt_auth_manager, get_settings, get_email_sender
from config.config import BaseAppSettings
from database import PasswordResetTokenModel
from database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    RefreshTokenModel,
)
from database.session import get_db
from database.utils import generate_secure_token
from schemas.accounts import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    MessageSchema,
    ChangePasswordRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetCompleteRequestSchema,
    LogoutRequestSchema,
    EmailRequestSchema,
)
from security.token_manager import JWTManager
from services import EmailSender

router = APIRouter()


def get_user_by_email(email, db: Session) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()


@router.post("/register/", response_model=UserRegistrationResponseSchema)
def create_user(
    user_data: UserRegistrationRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    settings: BaseAppSettings = Depends(get_settings),
) -> UserRegistrationResponseSchema:
    existing_user = db.query(UserModel).filter_by(email=user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    group = db.query(UserGroupModel).filter_by(name=UserGroupEnum.USER).first()

    try:
        new_user = UserModel.create(
            email=user_data.email,
            new_password=user_data.password,
            group_id=group.id,
        )
        db.add(new_user)
        db.flush()

        activation_token = ActivationTokenModel.create(
            user_id=new_user.id,
            token=generate_secure_token(),
            days=settings.ACTIVATION_TOKEN_LIFE,
        )
        db.add(activation_token)
        new_user.activation_token = activation_token

        db.commit()

        db.refresh(activation_token)
        token_value = activation_token.token

    except SQLAlchemyError as e:
        db.rollback()
        logging.error(f"DB Error: {e}")
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


@router.post("/resend-activation/", response_model=MessageSchema)
def resend_activation(
    user_data: EmailRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
    settings: BaseAppSettings = Depends(get_settings),
) -> MessageSchema:
    existing_user = get_user_by_email(user_data.email, db)

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if existing_user.is_active:
        return MessageSchema(message="User is already activated.")

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
            detail="An error occurred token creation.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_activation_email,
            user_data.email,
            token_value,
        )
    return MessageSchema(message="A new activation link has been sent.")


@router.get("/activate/", response_model=MessageSchema)
def activate_account(
    background_tasks: BackgroundTasks,
    email: EmailStr = Query(...),
    token: str = Query(...),
    email_sender: EmailSender = Depends(get_email_sender),
    db: Session = Depends(get_db),
):
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

    return MessageSchema(message="User account activated successfully.")


@router.post("/login/", response_model=UserLoginResponseSchema)
def login_user(
    user_data: UserLoginRequestSchema,
    db: Session = Depends(get_db),
    settings: BaseAppSettings = Depends(get_settings),
    jwt_manager: JWTManager = Depends(get_jwt_auth_manager),
) -> UserLoginResponseSchema:
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
        refresh_token = RefreshTokenModel.create(
            user_id=user.id, token=jwt_refresh_token, days=settings.LOGIN_DAYS
        )
        db.add(refresh_token)
        db.flush()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )

    jwt_access_token = jwt_manager.create_access_token(data={"user_id": user.id})
    return UserLoginResponseSchema(
        access_token=jwt_access_token, refresh_token=jwt_refresh_token
    )


@router.post("/logout/", response_model=MessageSchema)
def logout_user(
    user_data: LogoutRequestSchema, db: Session = Depends(get_db)
) -> MessageSchema:
    token_record = (
        db.query(RefreshTokenModel).filter_by(token=user_data.refresh_token).first()
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    try:
        db.delete(token_record)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout. Try again.",
        )

    return MessageSchema(message="Logged out successfully.")


@router.post("/change-password/", response_model=MessageSchema)
def change_password(
    user_data: ChangePasswordRequestSchema,
    db: Session = Depends(get_db),
) -> MessageSchema:
    user = get_user_by_email(user_data.email, db)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Error occurred."
        )

    if not user.verify_password(user_data.old_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user_data.old_password == user_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New password can not be same as the old one.",
        )

    try:
        user.password = user_data.new_password
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return MessageSchema(message="Password has been changed successfully!")


@router.post("/reset-password/request/", response_model=MessageSchema)
def reset_password_request(
    user_data: PasswordResetRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> MessageSchema:
    user = get_user_by_email(user_data.email, db)

    if not user or not user.is_active:
        return MessageSchema(
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

    return MessageSchema(
        message="If you have an account, you will receive an email with instructions."
    )


@router.post("/accounts/reset-password/complete/", response_model=MessageSchema)
def reset_password(
    user_data: PasswordResetCompleteRequestSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> MessageSchema:
    user = get_user_by_email(user_data.email, db)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or token."
        )

    token_record = db.query(PasswordResetTokenModel).filter_by(user_id=user.id).first()

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
            detail="Something went wrong.",
        )
    else:
        background_tasks.add_task(
            email_sender.send_password_reset_complete_email, user_data.email
        )

    return MessageSchema(message="Your password has been successfully changed!")
