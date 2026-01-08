import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database.db import db
from database.models import SearchHistory
from keyboards.pagination import hotel_nav_keyboard
from utils.formatting import format_hotel


async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    db.connect(reuse_if_open=True)
    rows = (SearchHistory
            .select()
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
            .limit(10))
    rows = list(rows)
    db.close()

    if not rows:
        await update.message.reply_text("History is empty. Run /lowprice first.")
        return

    buttons = []
    for r in rows:
        label = f"{r.created_at.strftime('%Y-%m-%d %H:%M')} | {r.command} | {r.city}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"hist_open|{r.id}")])

    await update.message.reply_text(
        "🕘 Your last searches (choose one):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def history_open_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    if len(data) != 2:
        await query.edit_message_text("Invalid history selection.")
        return

    hist_id = int(data[1])

    db.connect(reuse_if_open=True)
    r = SearchHistory.get_or_none(SearchHistory.id == hist_id)
    db.close()

    if not r:
        await query.edit_message_text("History item not found.")
        return

    hotels = json.loads(r.hotels_json)

    # put hotels into current session so your existing pagination works
    context.user_data["hotels"] = hotels
    context.user_data["hotel_index"] = 0

    await query.edit_message_text(
        f"✅ Loaded history:\n{r.command} | {r.city} | {r.checkin}→{r.checkout}\n\n"
        "Showing first hotel:",
    )
    await query.message.reply_text(
        format_hotel(hotels[0]),
        reply_markup=hotel_nav_keyboard(0, len(hotels))
    )


def build_history_handlers():
    return [
        CommandHandler("history", history_cmd),
        CallbackQueryHandler(history_open_callback, pattern=r"^hist_open\|\d+$"),
    ]
