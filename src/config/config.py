import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str = os.getenv("DB_USER", "test_user")
    DB_HOST: str = os.getenv("DB_HOST", "test_host")
    DB_PORT: int = os.getenv("DB_PORT", 5432)
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "test_password")
    DB_NAME: str = os.getenv("DB_NAME", "test_name")

    @property
    def DATABASE_URL(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
