from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from src.database import UserModel, ActivationTokenModel
from src.database.session import get_db
from src.schemas.common import MessageResponseSchema
from src.schemas.administration import BaseEmailSchema, ChangeGroupRequest
from src.dependencies import admin_required

router = APIRouter()


def get_user_by_email(email: EmailStr, db: Session):
    return db.query(UserModel).filter(UserModel.email == email).first()


@router.post(
    "/accounts/activate/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(admin_required)],
)
def admin_activate_user(
    data: BaseEmailSchema,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_active:
        return MessageResponseSchema(message="User account is already active")

    try:
        user.is_active = True
        db.query(ActivationTokenModel).filter(
            ActivationTokenModel.user_id == user.id
        ).delete()
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating user account",
        )

    return MessageResponseSchema(message="User account activated successfully by admin")


@router.post("/accounts/change-group/", response_model=MessageResponseSchema)
def change_user_group(
    data: ChangeGroupRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(admin_required),
):
    user = get_user_by_email(data.email, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Prevent changing the group of a user with the same ID as you.",
        )

    if user.group_id == data.group_id:
        return MessageResponseSchema(
            message=f"User already belongs to group {data.group_id}"
        )

    if data.group_id not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group ID"
        )

    try:
        user.group_id = data.group_id
        db.commit()

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return MessageResponseSchema(
        message=f"User group successfully changed to {data.group_id}."
    )
