from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from database.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
)
from database.session import get_db
from schemas.accounts import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
)
from security import hash_password

router = APIRouter()


@router.post("/register/", response_model=UserRegistrationResponseSchema)
def create_user(
    user_data: UserRegistrationRequestSchema,
    db: Session = Depends(get_db),
) -> UserRegistrationResponseSchema:
    existing_user = db.query(UserModel).filter_by(email=user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    group = db.query(UserGroupModel).filter_by(name=UserGroupEnum.USER).first()

    try:
        hashed_password = hash_password(user_data.password)

        new_user = UserModel(
            email=user_data.email,
            _hashed_password=hashed_password,
            group_id=group.id,
        )

        activation_token = ActivationTokenModel(user=new_user)
        new_user.activation_token = activation_token

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="An error occurred during user creation."
        )
    return UserRegistrationResponseSchema.model_validate(new_user)
