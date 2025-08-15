from pydantic import PostgresDsn

from src.config.config import BaseAppSettings


class PostgreSQLSettings(BaseAppSettings):
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    DB_HOST: str = "db"
    DB_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.DB_HOST,
                port=self.DB_PORT,
                path=self.POSTGRES_DB,
            )
        )
