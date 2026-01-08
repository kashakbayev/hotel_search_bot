from telegram import Update
from telegram.ext import ContextTypes

from keyboards.pagination import hotel_nav_keyboard
from utils.formatting import format_hotel
from services.booking_api import get_hotel_photos, get_description_and_info, BookingAPIError


def _current_hotel(context: ContextTypes.DEFAULT_TYPE):
    hotels = context.user_data.get("hotels") or []
    idx = int(context.user_data.get("hotel_index", 0))
    if not hotels:
        return None, [], 0, 0
    idx = max(0, min(idx, len(hotels) - 1))
    return hotels[idx], hotels, idx, len(hotels)


async def hotel_nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    hotel, hotels, idx, total = _current_hotel(context)
    if not hotel:
        await query.edit_message_text("No hotels cached. Run /lowprice again.")
        return

    data = query.data

    # ===== Prev/Next =====
    if data == "hotel_prev":
        idx = max(0, idx - 1)
        context.user_data["hotel_index"] = idx
        await query.edit_message_text(
            format_hotel(hotels[idx]),
            reply_markup=hotel_nav_keyboard(idx, total)
        )
        return

    if data == "hotel_next":
        idx = min(total - 1, idx + 1)
        context.user_data["hotel_index"] = idx
        await query.edit_message_text(
            format_hotel(hotels[idx]),
            reply_markup=hotel_nav_keyboard(idx, total)
        )
        return

    # ===== Photos =====
    if data == "hotel_photos":
        hotel_id = hotel.get("hotel_id")
        if not hotel_id:
            await query.message.reply_text("No hotel_id found for this item.")
            return

        try:
            resp = get_hotel_photos(str(hotel_id))
        except BookingAPIError as e:
            await query.message.reply_text(f"❌ Photos API error:\n{e}")
            return

        photos = (resp.get("data") or {}).get("photos") or []
        if not photos:
            await query.message.reply_text("No photos found for this hotel.")
            return

        # send first 3 photos (enough for TЗ)
        sent = 0
        for p in photos:
            url = p.get("url") or p.get("photoUrl") or p.get("mainUrl")
            if url:
                await query.message.reply_photo(url)
                sent += 1
            if sent >= 3:
                break
        if sent == 0:
            await query.message.reply_text("Photos exist but no usable URL fields found.")
        return

    # ===== Info / Description =====
    if data == "hotel_info":
        hotel_id = hotel.get("hotel_id")
        if not hotel_id:
            await query.message.reply_text("No hotel_id found for this item.")
            return

        try:
            resp = get_description_and_info(str(hotel_id), languagecode="en-us")
        except BookingAPIError as e:
            await query.message.reply_text(f"❌ Info API error:\n{e}")
            return

        data_obj = resp.get("data") or {}
        # часто описание лежит в одном из этих полей (зависит от провайдера)
        description = (
            data_obj.get("description") or
            data_obj.get("hotel_description") or
            data_obj.get("text") or
            ""
        )

        if not description:
            await query.message.reply_text("No description text found for this hotel.")
            return

        # Telegram limit-friendly
        description = description.strip()
        if len(description) > 3500:
            description = description[:3500] + "…"

        await query.message.reply_text(f"ℹ️ Description:\n\n{description}")
        return
