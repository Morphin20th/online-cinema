from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.params import Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette import status

from src.database import StarModel
from src.database.session import get_db
from src.dependencies import moderator_or_admin_required, get_current_user
from src.schemas.common import MessageResponseSchema
from src.schemas.movies import StarSchema, BaseStarSchema, StarListResponseSchema
from src.utils import build_pagination_links

router = APIRouter()


@router.post(
    "/create/",
    response_model=StarSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_201_CREATED,
)
def create_star(data: BaseStarSchema, db: Session = Depends(get_db)) -> StarSchema:
    existing_star = (
        db.query(StarModel).filter(StarModel.name.ilike(f"%{data.name}%")).first()
    )

    if existing_star:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A star with name {data.name} already exists.",
        )

    try:
        star = StarModel(name=data.name)
        db.add(star)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )

    return StarSchema.model_validate(star)


@router.get(
    "/{star_id}/",
    response_model=StarSchema,
    dependencies=[Depends(get_current_user)],
)
def get_star(star_id: int, db: Session = Depends(get_db)) -> StarSchema:
    existing_star = db.query(StarModel).filter(StarModel.id == star_id).first()

    if not existing_star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star with the given ID was not found.",
        )

    return StarSchema.model_validate(existing_star)


@router.patch(
    "/{star_id}/",
    response_model=StarSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def update_stars(
    star_id: int, data: BaseStarSchema, db: Session = Depends(get_db)
) -> StarSchema:
    star = db.query(StarModel).filter(StarModel.id == star_id).first()

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star with the given ID was not found.",
        )

    try:
        star.name = data.name
        db.commit()
        db.refresh(star)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return StarSchema.model_validate(star)


@router.delete(
    "/{star_id}/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(moderator_or_admin_required)],
)
def delete_star(star_id: int, db: Session = Depends(get_db)) -> MessageResponseSchema:
    star = db.query(StarModel).filter(StarModel.id == star_id).first()

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star with the given ID was not found.",
        )

    try:
        db.delete(star)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong.",
        )
    return MessageResponseSchema(message="Star has been deleted successfully.")


@router.get("/", response_model=StarListResponseSchema)
def get_stars(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
) -> StarListResponseSchema:
    offset = (page - 1) * per_page

    stars_query = db.query(StarModel)
    total_items = stars_query.count()

    stars = stars_query.offset(offset).limit(per_page).all()

    total_pages = (total_items + per_page - 1) // per_page
    prev_page, next_page = build_pagination_links(request, page, per_page, total_pages)

    stars_list = [StarSchema(id=star.id, name=star.name) for star in stars]

    return StarListResponseSchema(
        stars=stars_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items,
    )
