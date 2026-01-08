from database.init_db import init_db
from handlers.start import build_start_handler

from handlers.history import build_history_handlers
from handlers.help import build_help_handler

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from telegram.ext import CallbackQueryHandler
from handlers.pagination import hotel_nav_callback

from config import BOT_TOKEN
from handlers.search import build_search_conversation

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! ✅\nUse /lowprice to start hotel search.\n/cancel to stop.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - start\n"
        "/help - help\n"
        "/lowprice - search (city + dates)\n"
        "/cancel - cancel current flow"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(build_start_handler())

    # Add conversation
    app.add_handler(build_search_conversation())

    app.add_handler(CallbackQueryHandler(hotel_nav_callback, pattern="^hotel_"))

    for h in build_history_handlers():
        app.add_handler(h)

    app.add_handler(build_help_handler())
    init_db()

    app.run_polling()

if __name__ == "__main__":
    main()
