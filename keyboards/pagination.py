from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def hotel_nav_keyboard(index: int, total: int) -> InlineKeyboardMarkup:
    buttons = []

    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data="hotel_prev"))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data="hotel_next"))
    if nav_row:
        buttons.append(nav_row)

    # extra actions (required by TЗ: photos + description)
    buttons.append([
        InlineKeyboardButton("📷 Photos", callback_data="hotel_photos"),
        InlineKeyboardButton("ℹ️ Info", callback_data="hotel_info"),
    ])

    return InlineKeyboardMarkup(buttons)
