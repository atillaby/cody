from pydantic_settings import BaseSettings

class TelegramSettings(BaseSettings):
    BOT_TOKEN: str
    CHAT_ID: str
    NOTIFICATION_ENABLED: bool = True
    ALERT_LEVELS: dict = {
        "INFO": True,
        "WARNING": True,
        "ERROR": True,
        "CRITICAL": True
    }

    class Config:
        env_prefix = "TELEGRAM_"
