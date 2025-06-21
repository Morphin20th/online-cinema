from src.config.config import BaseAppSettings


class PaymentSettings(BaseAppSettings):
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
