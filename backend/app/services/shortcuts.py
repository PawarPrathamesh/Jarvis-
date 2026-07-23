from datetime import date

from app.repositories import grocery_expiry_summary, list_groceries


STORE_KEYWORDS = {"aldi", "rewe", "lidl", "netto", "edeka", "kaufland"}
STAPLES = ["eggs", "milk", "rice", "oats", "yogurt", "bananas"]


def build_location_alert(place: str, trigger: str, day: date | None = None) -> dict:
    target_day = day or date.today()
    place_name = place.strip() or "your location"
    normalized_place = place_name.lower()
    groceries = list_groceries()
    grocery_names = {item["name"].lower() for item in groceries}
    expiry = grocery_expiry_summary(target_day)

    urgent = expiry["expired"] + expiry["today"] + expiry["soon"]
    urgent_names = [item["name"] for item in urgent[:5]]
    missing_staples = [
        item
        for item in STAPLES
        if item not in grocery_names and item.rstrip("s") not in grocery_names
    ]

    is_store = any(store in normalized_place for store in STORE_KEYWORDS)
    if is_store:
        shopping = missing_staples[:5]
        actions = ["Open Jarvis dashboard", "Scan receipt after shopping"]
        if urgent_names:
            message = (
                f"You are near {place_name}. Buy {', '.join(shopping) if shopping else 'only essentials'}, "
                f"and plan meals around {', '.join(urgent_names[:3])} first."
            )
        else:
            message = (
                f"You are near {place_name}. "
                f"Suggested quick buy: {', '.join(shopping) if shopping else 'nothing urgent right now'}."
            )
    else:
        shopping = []
        actions = ["Ask Jarvis for today's briefing"]
        message = (
            f"Jarvis noticed you {trigger} {place_name}. "
            "No store-specific shopping alert is needed."
        )

    return {
        "title": f"Jarvis at {place_name}",
        "message": message,
        "shopping": shopping,
        "urgent_groceries": urgent_names,
        "actions": actions,
    }
