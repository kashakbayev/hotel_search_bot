from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

HELP_TEXT = (
    "🤖 Hotel Search Bot — commands:\n\n"
    "/start — start bot\n"
    "/help — show this help\n\n"
    "Search:\n"
    "/lowprice — find hotels (city + dates)\n"
    "/guest_rating — top by rating\n"
    "/bestdeal — best deal near center (distance + price)\n\n"
    "/history — show search history\n"
    "/cancel — cancel current search\n\n"
    "Tip: Use /lowprice to begin."
)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)

def build_help_handler() -> CommandHandler:
    return CommandHandler("help", help_cmd)

from keyboards.menu import main_menu_keyboard

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, reply_markup=main_menu_keyboard())