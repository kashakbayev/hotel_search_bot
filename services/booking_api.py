import requests
from config import RAPIDAPI_KEY

BASE_URL = "https://booking-com15.p.rapidapi.com"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com",
}

class BookingAPIError(Exception):
    pass


def get_destination(city: str) -> dict:
    """Return the best destination object for the given city."""
    url = f"{BASE_URL}/api/v1/hotels/searchDestination"
    params = {"query": city, "locale": "en-us"}

    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        raise BookingAPIError(f"Destination search failed: {r.status_code} {r.text}")

    data = r.json()
    items = data.get("data") or []
    if not items:
        raise BookingAPIError("No destinations found for this city.")

    # Prefer city
    city_item = next((x for x in items if (x.get("search_type") or "").lower() == "city"), items[0])
    if not city_item.get("dest_id"):
        raise BookingAPIError("dest_id not found in destination response.")
    if not city_item.get("search_type"):
        raise BookingAPIError("search_type not found in destination response.")

    return city_item

def search_destinations(query: str, limit: int = 5) -> list[dict]:
    """Return list of destination objects to show as keyboard choices."""
    url = f"{BASE_URL}/api/v1/hotels/searchDestination"
    params = {"query": query, "locale": "en-us"}

    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        raise BookingAPIError(f"Destination search failed: {r.status_code} {r.text}")

    data = r.json()
    items = data.get("data") or []
    if not items:
        return []

    # Prefer city results first, then others
    items_sorted = sorted(items, key=lambda x: 0 if (x.get("search_type") or "").lower() == "city" else 1)
    return items_sorted[:limit]

def search_hotels(dest_id: str, search_type: str, checkin: str, checkout: str,
                 adults: int = 2, page: int = 1):
    """
    Search hotels. search_type must match API (for you it's 'city').
    checkin/checkout: YYYY-MM-DD
    """
    url = f"{BASE_URL}/api/v1/hotels/searchHotels"
    params = {
        "dest_id": str(dest_id),
        "search_type": str(search_type),   # ✅ MUST be 'city' in your case
        "arrival_date": checkin,
        "departure_date": checkout,
        "adults": str(adults),
        "room_qty": "1",
        "page_number": str(page),
        "units": "metric",
        "temperature_unit": "c",
        "languagecode": "en-us",
        "currency_code": "USD",
    }

    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        raise BookingAPIError(f"Hotel search failed: {r.status_code} {r.text}")

    return r.json()

def get_hotel_photos(hotel_id: str):
    """
    GET /api/v1/hotels/getHotelPhotos
    hotel_id берётся из searchHotels (поле hotel_id).
    """
    url = f"{BASE_URL}/api/v1/hotels/getHotelPhotos"
    params = {"hotel_id": str(hotel_id)}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        raise BookingAPIError(f"getHotelPhotos failed: {r.status_code} {r.text}")
    return r.json()


def get_description_and_info(hotel_id: str, languagecode: str = "en-us"):
    """
    GET /api/v1/hotels/getDescriptionAndInfo
    """
    url = f"{BASE_URL}/api/v1/hotels/getDescriptionAndInfo"
    params = {"hotel_id": str(hotel_id), "languagecode": languagecode}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        raise BookingAPIError(f"getDescriptionAndInfo failed: {r.status_code} {r.text}")
    return r.json()

