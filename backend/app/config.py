from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./agentops.db"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    slack_webhook_url: str = ""
    alert_accuracy_threshold: float = 0.7
    alert_daily_cost_threshold: float = 50.0
    default_credit_on_payment: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
