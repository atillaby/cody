import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    OKX_API_KEY: str = os.getenv("OKX_API_KEY")
    OKX_SECRET_KEY: str = os.getenv("OKX_SECRET_KEY")
    OKX_PASSPHRASE: str = os.getenv("OKX_PASSPHRASE")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID")


@lru_cache()
def get_settings():
    return Settings()
