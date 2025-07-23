import os

from .settings import Settings, ProductionSettings, DevelopmentSettings, TestingSettings


def get_settings() -> Settings:
    """
    Dependency to get current application settings based on the ENVIRONMENT variable.

    Returns:
        Settings: An instance of ProductionSettings or DevelopmentSettings.
    """
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionSettings()
    elif env == "test":
        return TestingSettings()
    return DevelopmentSettings()


settings = get_settings()
