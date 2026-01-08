from telegram import ReplyKeyboardMarkup

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["/lowprice", "/guest_rating"],
        ["/bestdeal", "/history"],
        ["/help", "/cancel"],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Choose a command…"
    )
