from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from telegram_bot_calendar import DetailedTelegramCalendar

from services.booking_api import search_destinations, search_hotels, BookingAPIError
from keyboards.locations import locations_keyboard
from keyboards.pagination import hotel_nav_keyboard
from utils.formatting import format_hotel, get_hotel_price_value, get_guest_rating

import json
from database.db import db
from database.models import SearchHistory


# States
ASK_CITY, PICK_LOCATION, ASK_CHECKIN, ASK_CHECKOUT, ASK_MIN_PRICE, ASK_MAX_PRICE, ASK_MAX_DISTANCE = range(7)

# user_data keys
KEY_CITY = "city"
KEY_DEST_ID = "dest_id"
KEY_SEARCH_TYPE = "search_type"
KEY_CHECKIN = "checkin"
KEY_CHECKOUT = "checkout"
KEY_MIN_PRICE = "min_price"
KEY_MAX_PRICE = "max_price"
KEY_MAX_DISTANCE = "max_distance"
KEY_COMMAND = "command"


async def lowprice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data[KEY_COMMAND] = "lowprice"
    await update.message.reply_text("🏙️ Enter city name:")
    return ASK_CITY


async def city_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = (update.message.text or "").strip()
    if not city:
        await update.message.reply_text("Please enter a valid city name.")
        return ASK_CITY

    context.user_data[KEY_CITY] = city

    try:
        dests = search_destinations(city, limit=5)
    except BookingAPIError as e:
        await update.message.reply_text(f"❌ API error while searching city:\n{e}")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error:\n{e}")
        return ConversationHandler.END

    if not dests:
        await update.message.reply_text("No locations found. Try another city name.")
        return ASK_CITY

    context.user_data["destinations_cache"] = dests
    await update.message.reply_text(
        "📍 уточните локацию (выберите из списка):",
        reply_markup=locations_keyboard(dests),
    )
    return PICK_LOCATION


async def location_picked(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "loc_cancel":
        context.user_data.clear()
        await query.edit_message_text("Cancelled ❌")
        return ConversationHandler.END

    # expected: loc|dest_id|search_type
    parts = (query.data or "").split("|")
    if len(parts) != 3 or parts[0] != "loc":
        await query.edit_message_text("❌ Invalid selection. Try /lowprice again.")
        return ConversationHandler.END

    dest_id, search_type = parts[1], parts[2]
    context.user_data[KEY_DEST_ID] = dest_id
    context.user_data[KEY_SEARCH_TYPE] = search_type  # for you it will be 'city'

    cal = DetailedTelegramCalendar()
    markup, _ = cal.build()
    await query.edit_message_text("📅 Choose check-in date:", reply_markup=markup)
    return ASK_CHECKIN


async def checkin_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cal = DetailedTelegramCalendar()
    result, markup, step = cal.process(query.data)

    if not result:
        await query.edit_message_text(f"📅 Choose check-in date ({step}):", reply_markup=markup)
        return ASK_CHECKIN

    context.user_data[KEY_CHECKIN] = result

    cal2 = DetailedTelegramCalendar()
    markup2, _ = cal2.build()
    await query.edit_message_text(f"✅ Check-in: {result}\n\n📅 Choose check-out date:", reply_markup=markup2)
    return ASK_CHECKOUT


async def checkout_calendar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cal = DetailedTelegramCalendar()
    result, markup, step = cal.process(query.data)

    # still choosing date (year/month/day)
    if not result:
        await query.edit_message_text(
            f"📅 Choose check-out date ({step}):",
            reply_markup=markup
        )
        return ASK_CHECKOUT

    checkin = context.user_data.get(KEY_CHECKIN)
    checkout = result

    # validate checkout > checkin
    if checkin and checkout <= checkin:
        cal_retry = DetailedTelegramCalendar()
        retry_markup, _ = cal_retry.build()
        await query.edit_message_text(
            f"❗ Check-out must be after check-in.\n"
            f"Check-in: {checkin}\n\n"
            f"📅 Choose a new check-out date:",
            reply_markup=retry_markup
        )
        return ASK_CHECKOUT

    # save checkout
    context.user_data[KEY_CHECKOUT] = checkout

    # next step (required by TЗ): ask for min price
    await query.edit_message_text(
        "💰 Enter MIN price (number, e.g. 50).\n"
        "If you don't want a minimum limit, type 0:"
    )
    return ASK_MIN_PRICE

async def min_price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    try:
        min_price = float(text)
        if min_price < 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❗ Please enter a valid non-negative number for MIN price.")
        return ASK_MIN_PRICE

    context.user_data[KEY_MIN_PRICE] = min_price
    await update.message.reply_text(
        "💰 Enter MAX price (number, e.g. 300). If no limit, type 0:"
    )
    return ASK_MAX_PRICE


async def max_price_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    try:
        max_price = float(text)
        if max_price < 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❗ Please enter a valid non-negative number for MAX price.")
        return ASK_MAX_PRICE

    min_price = float(context.user_data.get(KEY_MIN_PRICE, 0))
    if max_price != 0 and max_price < min_price:
        await update.message.reply_text("❗ MAX price must be >= MIN price (or 0 for no limit). Try again:")
        return ASK_MAX_PRICE

    context.user_data[KEY_MAX_PRICE] = max_price

    # ✅ If command is bestdeal, ask distance first (no API call yet)
    command = context.user_data.get(KEY_COMMAND, "lowprice")
    if command == "bestdeal":
        await update.message.reply_text(
            "📍 Enter MAX distance to city center in km (e.g. 5).\n"
            "If no limit, type 0:"
        )
        return ASK_MAX_DISTANCE

    # ===== Otherwise (lowprice / guest_rating): call API now =====
    dest_id = context.user_data.get(KEY_DEST_ID)
    search_type = context.user_data.get(KEY_SEARCH_TYPE)  # usually 'city'
    checkin = context.user_data.get(KEY_CHECKIN)
    checkout = context.user_data.get(KEY_CHECKOUT)

    checkin_str = checkin.isoformat()
    checkout_str = checkout.isoformat()

    try:
        resp = search_hotels(
            dest_id=dest_id,
            search_type=search_type,
            checkin=checkin_str,
            checkout=checkout_str,
            adults=2,
            page=1,
        )
    except BookingAPIError as e:
        await update.message.reply_text(f"❌ API error:\n{e}")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error:\n{e}")
        return ConversationHandler.END

    hotels = (resp.get("data") or {}).get("hotels") or []
    if not hotels:
        await update.message.reply_text("No hotels found for these dates.")
        return ConversationHandler.END

    # ===== Filter by price range =====
    filtered = []
    for h in hotels:
        price_val = get_hotel_price_value(h)
        if price_val is None:
            continue

        ok_min = (min_price == 0) or (price_val >= min_price)
        ok_max = (max_price == 0) or (price_val <= max_price)

        if ok_min and ok_max:
            filtered.append(h)

    if not filtered:
        await update.message.reply_text(
            f"No hotels found in price range {min_price}–{max_price}.\nTry again."
        )
        return ConversationHandler.END

    # ===== Sort for guest_rating if needed =====
    if command == "guest_rating":
        filtered.sort(key=get_guest_rating, reverse=True)

    context.user_data["hotels"] = filtered
    context.user_data["hotel_index"] = 0

    await update.message.reply_text(
        format_hotel(filtered[0]),
        reply_markup=hotel_nav_keyboard(0, len(filtered))
    )
    return ConversationHandler.END

from utils.formatting import get_distance_km, get_hotel_price_value, format_hotel
# (если уже импортировано — просто добавь get_distance_km)

async def max_distance_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    try:
        max_dist = float(text)
        if max_dist < 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("❗ Please enter a valid non-negative number for distance (km).")
        return ASK_MAX_DISTANCE

    context.user_data[KEY_MAX_DISTANCE] = max_dist

    # ===== CALL API NOW (same as others) =====
    dest_id = context.user_data.get(KEY_DEST_ID)
    search_type = context.user_data.get(KEY_SEARCH_TYPE)
    checkin = context.user_data.get(KEY_CHECKIN)
    checkout = context.user_data.get(KEY_CHECKOUT)

    checkin_str = checkin.isoformat()
    checkout_str = checkout.isoformat()

    min_price = float(context.user_data.get(KEY_MIN_PRICE, 0))
    max_price = float(context.user_data.get(KEY_MAX_PRICE, 0))

    try:
        resp = search_hotels(
            dest_id=dest_id,
            search_type=search_type,
            checkin=checkin_str,
            checkout=checkout_str,
            adults=2,
            page=1,
        )
    except BookingAPIError as e:
        await update.message.reply_text(f"❌ API error:\n{e}")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Unexpected error:\n{e}")
        return ConversationHandler.END

    hotels = (resp.get("data") or {}).get("hotels") or []
    if not hotels:
        await update.message.reply_text("No hotels found for these dates.")
        return ConversationHandler.END

    # ===== FILTER BY PRICE + DISTANCE =====
    filtered = []
    for h in hotels:
        price_val = get_hotel_price_value(h)
        dist_km = get_distance_km(h)

        if price_val is None:
            continue
        if dist_km is None:
            continue  # bestdeal needs distance

        ok_min = (min_price == 0) or (price_val >= min_price)
        ok_max = (max_price == 0) or (price_val <= max_price)
        ok_dist = (max_dist == 0) or (dist_km <= max_dist)

        if ok_min and ok_max and ok_dist:
            filtered.append(h)

    if not filtered:
        await update.message.reply_text(
            f"No hotels found for your filters.\n"
            f"Price: {min_price}-{max_price}, Distance ≤ {max_dist} km.\n"
            "Try /bestdeal again."
        )
        return ConversationHandler.END

    # ===== SORT BESTDEAL: distance asc, then price asc =====
    filtered.sort(key=lambda h: (get_distance_km(h) or 9999, get_hotel_price_value(h) or 1e18))

    context.user_data["hotels"] = filtered
    context.user_data["hotel_index"] = 0

    await update.message.reply_text(
        format_hotel(filtered[0]),
        reply_markup=hotel_nav_keyboard(0, len(filtered))
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancelled ❌")
    return ConversationHandler.END

def build_search_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("lowprice", lowprice_start),
            CommandHandler("guest_rating", guest_rating_start),
            CommandHandler("bestdeal", bestdeal_start),
        ],
        states={
            ASK_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_received)],
            PICK_LOCATION: [CallbackQueryHandler(location_picked, pattern="^(loc\\|.*|loc_cancel)$")],
            ASK_CHECKIN: [CallbackQueryHandler(checkin_calendar_callback)],
            ASK_CHECKOUT: [CallbackQueryHandler(checkout_calendar_callback)],
            ASK_MIN_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_price_received)],
            ASK_MAX_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_price_received)],
            ASK_MAX_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_distance_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

async def guest_rating_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data[KEY_COMMAND] = "guest_rating"
    await update.message.reply_text("🏙️ Enter city name:")
    return ASK_CITY

async def bestdeal_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data[KEY_COMMAND] = "bestdeal"
    await update.message.reply_text("🏙️ Enter city name:")
    return ASK_CITY


