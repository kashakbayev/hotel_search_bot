def format_hotel(hotel: dict) -> str:
    hotel_id = hotel.get("hotel_id")
    prop = hotel.get("property") or {}

    name = prop.get("name") or prop.get("wishlistName") or "Hotel"
    lat = prop.get("latitude")
    lon = prop.get("longitude")

    pb = prop.get("priceBreakdown") or {}
    gross = (pb.get("grossPrice") or {}).get("value")
    currency = (pb.get("grossPrice") or {}).get("currency", "")

    checkin = prop.get("checkinDate") or ""
    checkout = prop.get("checkoutDate") or ""

    price_text = f"{gross:.2f} {currency}" if isinstance(gross, (int, float)) else "-"

    short_desc = (hotel.get("accessibilityLabel") or "").strip()
    if len(short_desc) > 350:
        short_desc = short_desc[:350] + "…"

    return (
        f"🏨 {name}\n"
        f"🆔 hotel_id: {hotel_id}\n"
        f"💰 Price: {price_text}\n"
        f"📅 Dates: {checkin} → {checkout}\n"
        f"📍 Coordinates: {lat}, {lon}\n\n"
        f"{short_desc}"
    )


def get_hotel_price_value(hotel: dict):
    """
    Returns numeric price (float) if present, else None.
    booking-com15: hotel['property']['priceBreakdown']['grossPrice']['value']
    """
    prop = hotel.get("property") or {}
    pb = prop.get("priceBreakdown") or {}
    gross = pb.get("grossPrice") or {}
    val = gross.get("value")
    return float(val) if isinstance(val, (int, float)) else None

def get_guest_rating(hotel: dict):
    """
    Extract guest rating as float.
    booking-com15 usually stores it inside accessibilityLabel text.
    Example: '8.9 Excellent 2249 reviews'
    """
    label = hotel.get("accessibilityLabel") or ""
    for part in label.split():
        try:
            return float(part)
        except ValueError:
            continue
    return 0.0

import re

def get_distance_km(hotel: dict):
    """
    Tries to extract distance to downtown from accessibilityLabel.
    Example part: "‎2.8 km from downtown‬"
    Returns float km or None.
    """
    label = hotel.get("accessibilityLabel") or ""
    # ищем число + 'km from downtown'
    m = re.search(r"(\d+(?:\.\d+)?)\s*km\s+from\s+downtown", label, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except:
        return None

