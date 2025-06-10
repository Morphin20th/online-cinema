import os
import uuid
from datetime import date

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import get_settings
from database.models.accounts import GenderEnum, UserProfileModel, UserModel
from database.session import get_db
from schemas.profiles import ProfileSchema
from security.dependencies import get_current_user, get_current_active_user
from validation.profile_validators import (
    validate_name,
    validate_birth_date,
    validate_gender,
    validate_image,
)

router = APIRouter()

MEDIA_DIR = get_settings().PROJECT_ROOT / "src" / "storage" / "media" / "avatars"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def is_user_authorized(user_id: int, token_user_id: int, group_id: int) -> bool:
    return token_user_id == user_id or group_id == 1


def save_avatar(file: UploadFile, user_id: int) -> str:
    extension = file.filename.split(".")[-1].lower()
    unique_filename = f"user_{user_id}_{uuid.uuid4().hex}.{extension}"
    file_path = MEDIA_DIR / unique_filename

    with open(file_path, "wb") as out_file:
        out_file.write(file.file.read())

    return f"/media/avatars/{unique_filename}"


@router.post(
    "/users/{user_id}/profile/",
    response_model=ProfileSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    first_name: str = Form(None),
    last_name: str = Form(None),
    avatar: UploadFile = File(None),
    gender: str = Form(None),
    date_of_birth: date = Form(None),
    info: str = Form(None),
    db: Session = Depends(get_db),
):
    if current_user.group_id != 1 and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create your own profile",
        )

    try:
        if first_name:
            validate_name(first_name)
        if last_name:
            validate_name(last_name)
        if date_of_birth:
            validate_birth_date(date_of_birth)
        if gender:
            validate_gender(gender)
        if info is not None and not info.strip():
            raise ValueError("Info field cannot be empty or contain only spaces.")
        if avatar:
            validate_image(avatar)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    target_user = db.query(UserModel).filter_by(id=user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    existing_profile = db.query(UserProfileModel).filter_by(user_id=user_id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Profile already exists."
        )

    avatar_path = save_avatar(avatar, user_id) if avatar else ""

    try:
        profile = UserProfileModel(
            user_id=user_id,
            first_name=first_name or "",
            last_name=last_name or "",
            avatar=avatar_path,
            gender=GenderEnum(gender) if gender else None,
            date_of_birth=date_of_birth,
            info=info or "",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile",
        )

    return profile


@router.patch(
    "/users/{user_id}/profile/",
    response_model=ProfileSchema,
    status_code=status.HTTP_200_OK,
)
def update_profile(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    first_name: str = Form(None),
    last_name: str = Form(None),
    avatar: UploadFile = File(None),
    gender: str = Form(None),
    date_of_birth: date = Form(None),
    info: str = Form(None),
    db: Session = Depends(get_db),
):
    if current_user.group_id != 1 and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or profile owner can update profile",
        )

    profile = db.query(UserProfileModel).filter_by(user_id=user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    try:
        if first_name:
            validate_name(first_name)
            profile.first_name = first_name
        if last_name:
            validate_name(last_name)
            profile.last_name = last_name
        if gender:
            validate_gender(gender)
            profile.gender = GenderEnum(gender)
        if date_of_birth:
            validate_birth_date(date_of_birth)
            profile.date_of_birth = date_of_birth
        if info is not None:
            if not info.strip():
                raise ValueError("Info cannot be empty or whitespace only")
            profile.info = info
        if avatar:
            validate_image(avatar)
            old_avatar_path = (
                get_settings().PROJECT_ROOT / "src" / profile.avatar.strip("/")
            )
            if old_avatar_path.exists():
                os.remove(old_avatar_path)
            profile.avatar = save_avatar(avatar, user_id)

        db.commit()
        db.refresh(profile)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        )

    return profile


@router.get(
    "/users/{user_id}/profile",
    response_model=ProfileSchema,
    status_code=status.HTTP_200_OK,
)
def get_user_profile(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.group_id != 1 and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or profile owner can view profile",
        )

    profile = db.query(UserProfileModel).filter_by(user_id=user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    return profile
