import logging
import asyncio
import sys  # sys modülünü import edelim
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from pathlib import Path
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, token: str, strategy_service, portfolio_manager):
        self.token = token
        self.strategy_service = strategy_service
        self.portfolio_manager = portfolio_manager
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("portfolio", self.portfolio))
        self.app.add_handler(CommandHandler("signals", self.signals))
        self.app.add_handler(CommandHandler("trades", self.trades))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [
                InlineKeyboardButton("📊 Portfolio", callback_data="portfolio"),
                InlineKeyboardButton("🎯 Active Signals", callback_data="signals")
            ],
            [
                InlineKeyboardButton("💹 Open Trades", callback_data="trades"),
                InlineKeyboardButton("📈 Stats", callback_data="stats")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.effective_message.reply_text(
            "🤖 *Trading Bot Control Panel*\n\n"
            "Select an option from the menu below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            portfolio_data = await self.portfolio_manager.get_portfolio()
            total_value = await self.portfolio_manager.get_portfolio_value()

            message = "💼 *Portfolio Status*\n\n"
            message += f"Total Value: ${total_value:,.2f}\n\n"

            for asset, amount in portfolio_data.items():
                if float(amount) > 0:
                    message += f"*{asset}*: {float(amount):,.8f}\n"

            await update.effective_message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Portfolio error: {e}")
            await update.effective_message.reply_text("❌ Error fetching portfolio data")

    async def signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            signals = await self.strategy_service.get_active_signals()
            if not signals:
                await update.effective_message.reply_text("📊 No active signals")
                return

            message = "🎯 *Active Signals*\n\n"
            for signal in signals:
                message += (
                    f"*{signal['symbol']}*\n"
                    f"Type: {signal['type']}\n"
                    f"Price: ${signal['price']:,.2f}\n"
                    f"Strategy: {signal['strategy']}\n\n"
                )

            await update.effective_message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Signals error: {e}")
            await update.effective_message.reply_text("❌ Error fetching signals")

    async def trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            trades = await self.strategy_service.get_open_trades()
            if not trades:
                await update.effective_message.reply_text("💹 No open trades")
                return

            message = "📊 *Open Trades*\n\n"
            for trade in trades:
                pnl = trade.get('unrealized_pnl', 0)
                message += (
                    f"*{trade['symbol']}*\n"
                    f"Side: {trade['side']}\n"
                    f"Entry: ${trade['entry_price']:,.2f}\n"
                    f"Current: ${trade['current_price']:,.2f}\n"
                    f"PNL: {pnl:+.2f}%\n\n"
                )

            await update.effective_message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Trades error: {e}")
            await update.effective_message.reply_text("❌ Error fetching trades")

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            stats = await self.strategy_service.get_stats()
            message = "📈 *Trading Statistics*\n\n"
            message += (
                f"Total Trades: {stats['total_trades']}\n"
                f"Win Rate: {stats['win_rate']:.2f}%\n"
                f"Profit Factor: {stats['profit_factor']:.2f}\n"
                f"Max Drawdown: {stats['max_drawdown']:.2f}%\n"
                f"Best Trade: {stats['best_trade']:.2f}%\n"
                f"Worst Trade: {stats['worst_trade']:.2f}%\n"
            )

            await update.effective_message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Stats error: {e}")
            await update.effective_message.reply_text("❌ Error fetching statistics")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "portfolio":
            await self.portfolio(update, context)
        elif query.data == "signals":
            await self.signals(update, context)
        elif query.data == "trades":
            await self.trades(update, context)
        elif query.data == "stats":
            await self.stats(update, context)

    def run(self):
        logger.info("Starting Telegram bot...")
        self.app.run_polling()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Configure logging
    log_path = Path(__file__).parent.parent.parent / "logs" / "telegram.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)],
    )

    # Initialize services
    from api.services.strategy_service import StrategyService
    from api.services.portfolio_manager import PortfolioManager
    from api.services.okx_service import OKXService
    from api.services.telegram_service import TelegramService
    from api.config.settings import get_settings

    settings = get_settings()
    okx_service = OKXService()
    telegram_service = TelegramService()
    strategy_service = StrategyService(okx_service, telegram_service)
    portfolio_manager = PortfolioManager(okx_service)

    # Start the bot
    bot = TradingBot(
        token=settings.TELEGRAM_BOT_TOKEN,
        strategy_service=strategy_service,
        portfolio_manager=portfolio_manager
    )
    bot.run()
