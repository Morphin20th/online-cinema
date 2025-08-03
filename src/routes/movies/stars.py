from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import StarModel, get_db
from src.dependencies import moderator_or_admin_required, get_current_user
from src.schemas import (
    CURRENT_USER_EXAMPLES,
    MODERATOR_OR_ADMIN_EXAMPLES,
    MessageResponseSchema,
    StarSchema,
    BaseStarSchema,
    StarListResponseSchema,
)
from src.utils import Paginator, aggregate_error_examples

router = APIRouter()


@router.post(
    "/create/",
    response_model=StarSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_201_CREATED,
    summary="Create Star",
    description="Endpoint for creating stars",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_409_CONFLICT: aggregate_error_examples(
            description="Conflict",
            examples={"star_exists": "A star with name 'test name' already exists."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred while trying to create star."},
        ),
    },
)
def create_star(data: BaseStarSchema, db: Session = Depends(get_db)) -> StarSchema:
    """Create a new star (actor or actress). Only for moderators or admins.

    Args:
        data: Star name to be created.
        db: Database session.

    Returns:
        Created star object.
    """
    existing_star = (
        db.query(StarModel).filter(StarModel.name.ilike(f"%{data.name}%")).first()
    )

    if existing_star:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A star with name '{data.name}' already exists.",
        )

    try:
        star = StarModel(name=data.name)
        db.add(star)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occurred while trying to create star.",
        )

    return StarSchema.model_validate(star)


@router.get(
    "/{star_id}/",
    response_model=StarSchema,
    dependencies=[Depends(get_current_user)],
    status_code=status.HTTP_200_OK,
    summary="Get Star Detail",
    description="Endpoint for getting star details",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user."},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_star_found": "Star with the given ID was not found."},
        ),
    },
)
def get_star(star_id: int, db: Session = Depends(get_db)) -> StarSchema:
    """Get a star by ID. Available for authenticated users.

    Args:
        star_id: ID of the star to retrieve.
        db: Database session.

    Returns:
        Star object.
    """
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
    status_code=status.HTTP_200_OK,
    summary="Update Star",
    description="Endpoint for updating star",
    responses={
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_star_found": "Star with the given ID was not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred while trying to update star."},
        ),
    },
)
def update_stars(
    star_id: int, data: BaseStarSchema, db: Session = Depends(get_db)
) -> StarSchema:
    """Update a star by ID. Only for moderators or admins.

    Args:
        star_id: ID of the star to update.
        data: Updated star data.
        db: Database session.

    Returns:
        Updated star object.
    """
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
            detail="Error occurred while trying to update star.",
        )
    return StarSchema.model_validate(star)


@router.delete(
    "/{star_id}/",
    response_model=MessageResponseSchema,
    dependencies=[Depends(moderator_or_admin_required)],
    status_code=status.HTTP_200_OK,
    summary="Delete Star",
    description="Endpoint for deleting star",
    responses={
        status.HTTP_200_OK: aggregate_error_examples(
            description="OK",
            examples={"message": "Star has been deleted successfully."},
        ),
        status.HTTP_401_UNAUTHORIZED: aggregate_error_examples(
            description="Unauthorized", examples=CURRENT_USER_EXAMPLES
        ),
        status.HTTP_403_FORBIDDEN: aggregate_error_examples(
            description="Forbidden",
            examples={"inactive_user": "Inactive user.", **MODERATOR_OR_ADMIN_EXAMPLES},
        ),
        status.HTTP_404_NOT_FOUND: aggregate_error_examples(
            description="Not Found",
            examples={"no_star_found": "Star with the given ID was not found."},
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: aggregate_error_examples(
            description="Internal Server Error",
            examples={"internal_server": "Error occurred while trying to delete star."},
        ),
    },
)
def delete_star(star_id: int, db: Session = Depends(get_db)) -> MessageResponseSchema:
    """Delete a star by ID. Only for moderators or admins.

    Args:
        star_id: ID of the star to delete.
        db: Database session.

    Returns:
        Message response indicating successful deletion.
    """
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
            detail="Error occurred while trying to delete star.",
        )
    return MessageResponseSchema(message="Star has been deleted successfully.")


@router.get(
    "/",
    response_model=StarListResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Stars List",
    description="Endpoint for getting stars list",
)
def get_stars(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based index)"),
    per_page: int = Query(10, ge=1, le=20, description="Number of items per page"),
    db: Session = Depends(get_db),
) -> StarListResponseSchema:
    """Get a list of all stars. Available for everyone.

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        per_page: Number of items per page.
        db: Database session.

    Returns:
        Paginated list of stars.
    """
    query = db.query(StarModel)

    paginator = Paginator(request, query, page, per_page)
    stars = paginator.paginate().all()
    prev_page, next_page = paginator.get_links()

    stars_list = [StarSchema(id=star.id, name=star.name) for star in stars]

    return StarListResponseSchema(
        stars=stars_list,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=paginator.total_pages,
        total_items=paginator.total_items,
    )
