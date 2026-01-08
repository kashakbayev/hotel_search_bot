from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from keyboards.menu import main_menu_keyboard

WELCOME_TEXT = (
    "👋 Welcome to Hotel Bot!\n\n"
    "I can help you find hotels using Booking data.\n"
    "Choose a command below:\n\n"
    "🔎 /lowprice — cheapest hotels\n"
    "⭐ /guest_rating — top by guest rating\n"
    "📍 /bestdeal — best near city center (distance + price)\n"
    "🕘 /history — your search history\n"
    "ℹ️ /help — how it works"
)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())

def build_start_handler() -> CommandHandler:
    return CommandHandler("start", start_cmd)
