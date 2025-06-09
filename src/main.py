from fastapi import FastAPI

from routes import account_router, profile_router

app = FastAPI(
    title="Online Cinema",
    description="Online Cinema project implemented using FastAPI and SQlAlchemy",
)

app.include_router(account_router, prefix=f"/accounts", tags=["accounts"])
app.include_router(profile_router, prefix="/profiles", tags=["profiles"])
