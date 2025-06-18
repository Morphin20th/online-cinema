from fastapi import FastAPI

from src.routes import (
    account_router,
    profile_router,
    admin_router,
    movie_router,
    cart_router,
)

app = FastAPI(
    title="Online Cinema",
    description="Online Cinema project implemented using FastAPI and SQlAlchemy",
)

app.include_router(account_router, prefix=f"/accounts", tags=["accounts"])
app.include_router(profile_router, prefix="/profiles", tags=["profiles"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(movie_router, prefix="/movies", tags=["movies"])
app.include_router(cart_router, prefix="/cart", tags=["cart"])
