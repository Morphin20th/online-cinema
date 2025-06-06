from fastapi import FastAPI

from routes import account_router

app = FastAPI(
    title="Online Cinema",
    description="Online Cinema project implemented using FastAPI and SQlAlchemy",
)

app.include_router(account_router, prefix=f"/accounts", tags=["accounts"])
