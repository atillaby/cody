import logging

from fastapi import FastAPI

from api.config import get_settings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI uygulaması
app = FastAPI(title="Telegram Bot Service")

settings = get_settings()

# Telegram bot uygulaması
bot = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()


@app.on_event("startup")
async def startup_event():
    """Uygulama başlatıldığında çalışacak fonksiyon"""
    logger.info("Telegram service starting...")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegram /start komutu"""
    await update.message.reply_text("Trading bot başlatıldı! Sinyaller için hazırım.")


# Komut handler'larını ekle
bot.add_handler(CommandHandler("start", start_command))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
