import uuid
from datetime import date

from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import get_jwt_auth_manager, get_settings
from database.models.accounts import GenderEnum, UserProfileModel, UserModel
from database.session import get_db
from schemas.profiles import ProfileSchema
from security.dependencies import get_token
from security.token_manager import JWTManager
from validation.profile_validators import (
    validate_name,
    validate_birth_date,
    validate_gender,
    validate_image,
)

router = APIRouter()

MEDIA_DIR = get_settings().PROJECT_ROOT / "src" / "storage" / "media" / "avatars"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


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
    first_name: str = Form(...),
    last_name: str = Form(...),
    avatar: UploadFile = File(...),
    gender: str = Form(...),
    date_of_birth: date = Form(...),
    info: str = Form(...),
    db: Session = Depends(get_db),
    authorization: str = Depends(get_token),
    jwt_manager: JWTManager = Depends(get_jwt_auth_manager),
):
    try:
        payload = jwt_manager.decode_token(authorization)
        token_user_id = payload.get("user_id")
        if token_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user access"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        validate_name(first_name)
        validate_name(last_name)
        validate_birth_date(date_of_birth)
        validate_gender(gender)

        if not info.strip():
            raise ValueError("Info field cannot be empty or contain only spaces.")

        validate_image(avatar)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    user = db.query(UserModel).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    avatar_path = save_avatar(avatar, user_id)

    try:
        profile = UserProfileModel(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            avatar=avatar_path,
            gender=GenderEnum(gender),
            date_of_birth=date_of_birth,
            info=info,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )

    return profile
