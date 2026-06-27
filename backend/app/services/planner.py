from datetime import date, datetime

from app.schemas import DailyBriefing, WeatherSummary


PROTEIN_PRIORITY = ["chicken", "tofu", "lentils", "beans", "tuna", "eggs", "egg", "yogurt"]
CARB_PRIORITY = ["rice", "pasta", "potatoes", "wraps", "bread", "oats"]
VEG_PRIORITY = ["tomatoes", "tomato", "spinach", "pepper", "onion", "broccoli", "salad"]


def build_daily_briefing(
    weather: WeatherSummary,
    groceries: list[dict],
    wardrobe: list[dict],
    schedule: list[dict],
    day: date,
) -> DailyBriefing:
    has_sport = any(item["activity_type"] in {"football", "gym", "sport"} for item in schedule)
    schedule_lines = [_format_schedule_item(item) for item in schedule]
    outfit = _choose_outfit(weather, wardrobe, has_sport)
    meals = _choose_meals(groceries, has_sport)
    shopping = _build_shopping_list(groceries, schedule)
    alerts = _build_alerts(weather, groceries, schedule, day)

    return DailyBriefing(
        greeting="Good morning, I am Jarvis. Here is your student briefing for today.",
        weather=weather,
        schedule=schedule_lines,
        outfit=outfit,
        meals=meals,
        shopping=shopping,
        alerts=alerts,
    )


def _format_schedule_item(item: dict) -> str:
    start = datetime.fromisoformat(item["starts_at"]).strftime("%H:%M")
    end = datetime.fromisoformat(item["ends_at"]).strftime("%H:%M")
    location = f" at {item['location']}" if item.get("location") else ""
    return f"{start}-{end}: {item['title']}{location}"


def _choose_outfit(weather: WeatherSummary, wardrobe: list[dict], has_sport: bool) -> list[str]:
    rain = weather.rain_mm > 0 or weather.precipitation_probability >= 50
    cold = weather.temperature_c <= 10
    warm = weather.temperature_c >= 24

    selected: list[str] = []
    types_needed = ["jacket", "top", "bottom", "shoes"]

    for item_type in types_needed:
        if item_type == "jacket" and warm and not rain:
            selected.append("no jacket needed; keep the outfit light")
            continue
        candidates = [item for item in wardrobe if item["item_type"] == item_type]
        if not candidates:
            continue
        ranked = sorted(
            candidates,
            key=lambda item: _score_wardrobe_item(item, rain=rain, cold=cold, warm=warm),
            reverse=True,
        )
        selected.append(ranked[0]["name"])

    if has_sport:
        sport_items = [
            item["name"]
            for item in wardrobe
            if item["sport_ready"] and item["name"] not in selected
        ]
        selected.extend(sport_items[:2])

    return selected


def _score_wardrobe_item(item: dict, rain: bool, cold: bool, warm: bool) -> int:
    score = 0
    if rain and item["rain_ready"]:
        score += 4
    if cold:
        score += int(item["warmth"]) * 2
    if warm:
        score -= int(item["warmth"])
    if "minimal" in item["style"] or "casual" in item["style"]:
        score += 1
    return score


def _choose_meals(groceries: list[dict], has_sport: bool) -> dict[str, str]:
    names = {item["name"].lower() for item in groceries}
    protein = _first_matching(names, PROTEIN_PRIORITY) or "eggs"
    carb = _first_matching(names, CARB_PRIORITY) or "rice"
    vegetable = _first_matching(names, VEG_PRIORITY) or "tomatoes"

    breakfast = "oats with banana and yogurt" if {"oats", "banana", "yogurt"} & names else "quick eggs and toast"
    lunch = f"{carb} bowl with {vegetable} and {protein}"
    dinner = f"high-protein {protein} {carb} bowl" if has_sport else f"simple {carb} with {vegetable}"

    return {
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner,
    }


def _first_matching(names: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in names:
            return candidate
    return None


def _build_shopping_list(groceries: list[dict], schedule: list[dict]) -> list[str]:
    names = {item["name"].lower() for item in groceries}
    staples = ["eggs", "milk", "rice", "oats", "yogurt", "bananas"]
    missing = [item for item in staples if item not in names and item.rstrip("s") not in names]
    near_store = next((item.get("near_store") for item in schedule if item.get("near_store")), None)

    if near_store and missing:
        return [f"After lecture near {near_store}, buy {', '.join(missing[:4])}."]
    return [f"Buy {item}." for item in missing[:4]]


def _build_alerts(
    weather: WeatherSummary,
    groceries: list[dict],
    schedule: list[dict],
    day: date,
) -> list[str]:
    alerts: list[str] = []
    if weather.rain_mm > 0 or weather.precipitation_probability >= 50:
        alerts.append("Carry an umbrella or waterproof jacket.")
    if weather.wind_kmh >= 25:
        alerts.append("It is windy, so prefer a secure outer layer.")

    for item in groceries:
        expires_on = item.get("expires_on")
        if not expires_on:
            continue
        days_left = (date.fromisoformat(expires_on) - day).days
        if days_left <= 1:
            alerts.append(f"Use {item['name']} soon, it expires in {max(days_left, 0)} day(s).")

    if any(item["activity_type"] == "football" for item in schedule):
        alerts.append("You have football today, so keep dinner higher in protein and carbs.")

    return alerts
