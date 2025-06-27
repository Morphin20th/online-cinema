from fastapi import FastAPI

from src.dependencies import get_settings
from src.routes import (
    account_router,
    profile_router,
    admin_router,
    movie_router,
    cart_router,
    order_router,
    payment_router,
)

settings = get_settings()

app = FastAPI(
    title="Online Cinema",
    description="Online Cinema project implemented using FastAPI and SQlAlchemy",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

app.include_router(account_router, prefix="/accounts", tags=["accounts"])
app.include_router(profile_router, prefix="/profiles", tags=["profiles"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(movie_router, prefix="/movies", tags=["movies"])
app.include_router(cart_router, prefix="/cart", tags=["cart"])
app.include_router(order_router, prefix="/orders", tags=["order"])
app.include_router(payment_router, prefix="/payments", tags=["payment"])
