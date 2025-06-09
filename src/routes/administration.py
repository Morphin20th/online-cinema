from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from database import UserModel, ActivationTokenModel
from database.session import get_db
from schemas.accounts import MessageSchema
from security.dependencies import check_admin_role

router = APIRouter()


@router.post("/accounts/activate/", response_model=MessageSchema)
def admin_activate_user(
    email: EmailStr,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(check_admin_role),
):
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_active:
        return MessageSchema(message="User account is already active")

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

    return MessageSchema(message="User account activated successfully by admin")
