from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def locations_keyboard(destinations: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for d in destinations:
        label = d.get("label") or d.get("name") or "Unknown"
        dest_id = d.get("dest_id")
        search_type = d.get("search_type")

        # callback_data must be short -> store only essential
        # format: loc|dest_id|search_type
        cb = f"loc|{dest_id}|{search_type}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb)])

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="loc_cancel")])
    return InlineKeyboardMarkup(buttons)
