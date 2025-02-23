import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        logger.info(
            f"Telegram notifications {'enabled' if self.enabled else 'disabled'}"
        )

    async def send_message(self, text: str):
        """Send plain text message"""
        if not self.enabled:
            logger.info(f"Telegram message (disabled): {text}")
            return

        logger.info(f"Telegram message: {text}")
        # Telegram API çağrısı burada yapılacak
        # requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", data={"chat_id": self.chat_id, "text": text})

    async def send_alert(self, strategy_name: str, action: str, price: float):
        """Send trading alert to Telegram"""
        if not self.enabled:
            logger.info(
                f"Telegram alert (disabled): {strategy_name} - {action} at {price}"
            )
            return

        message = f"🤖 {strategy_name}\n"
        message += f"Signal: {action}\n"
        message += f"Price: ${price:,.2f}"

        logger.info(f"Telegram alert: {message}")
        # Telegram API çağrısı burada yapılacak
        # requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", data={"chat_id": self.chat_id, "text": message})
