from datetime import date, datetime

from app.schemas import DailyBriefing, MealRecommendation, OutfitChoice, WeatherSummary


PROTEIN_PRIORITY = ["chicken", "tofu", "lentils", "beans", "tuna", "eggs", "egg", "yogurt"]
CARB_PRIORITY = ["rice", "pasta", "potatoes", "wraps", "bread", "oats"]
VEG_PRIORITY = ["tomatoes", "tomato", "spinach", "pepper", "onion", "broccoli", "salad"]
NEUTRAL_COLORS = {"black", "white", "grey", "gray", "dark blue", "navy", "beige", "cream"}
COLOR_FAMILIES = {
    "black": {"black", "white", "grey", "gray", "dark blue", "navy", "olive", "beige"},
    "white": {"black", "grey", "gray", "dark blue", "navy", "blue", "beige"},
    "grey": {"black", "white", "dark blue", "navy", "blue", "olive"},
    "gray": {"black", "white", "dark blue", "navy", "blue", "olive"},
    "dark blue": {"black", "white", "grey", "gray", "blue", "beige"},
    "navy": {"black", "white", "grey", "gray", "blue", "beige"},
    "blue": {"white", "grey", "gray", "dark blue", "navy", "beige"},
    "olive": {"black", "white", "grey", "gray", "beige"},
    "beige": {"black", "white", "dark blue", "navy", "olive"},
}


def build_daily_briefing(
    weather: WeatherSummary,
    groceries: list[dict],
    wardrobe: list[dict],
    schedule: list[dict],
    day: date,
) -> DailyBriefing:
    has_sport = any(item["activity_type"] in {"football", "gym", "sport"} for item in schedule)
    has_formal = any(
        any(word in item["title"].lower() for word in ["presentation", "interview", "exam"])
        for item in schedule
    )
    schedule_lines = [_format_schedule_item(item) for item in schedule]
    outfit_details = _choose_outfit(weather, wardrobe, has_sport, has_formal)
    outfit = [item.name for item in outfit_details]
    meal_details = _choose_meal_details(groceries, schedule, has_sport, day)
    meals = {item.meal: item.name for item in meal_details}
    shopping = _build_shopping_list(groceries, schedule)
    alerts = _build_alerts(weather, groceries, schedule, day)

    return DailyBriefing(
        greeting="Good morning, I am Jarvis. Here is your student briefing for today.",
        weather=weather,
        schedule=schedule_lines,
        outfit=outfit,
        outfit_details=outfit_details,
        meals=meals,
        meal_details=meal_details,
        shopping=shopping,
        alerts=alerts,
    )


def _format_schedule_item(item: dict) -> str:
    start = datetime.fromisoformat(item["starts_at"]).strftime("%H:%M")
    end = datetime.fromisoformat(item["ends_at"]).strftime("%H:%M")
    location = f" at {item['location']}" if item.get("location") else ""
    return f"{start}-{end}: {item['title']}{location}"


def _choose_outfit(
    weather: WeatherSummary,
    wardrobe: list[dict],
    has_sport: bool,
    has_formal: bool,
) -> list[OutfitChoice]:
    rain = weather.rain_mm > 0 or weather.precipitation_probability >= 50
    cold = weather.temperature_c <= 10
    warm = weather.temperature_c >= 24

    selected: list[OutfitChoice] = []
    selected_items: list[dict] = []
    types_needed = ["jacket", "top", "bottom", "shoes"]

    for item_type in types_needed:
        if item_type == "jacket" and warm and not rain:
            selected.append(
                OutfitChoice(
                    name="no jacket needed; keep the outfit light",
                    item_type="jacket",
                    color=None,
                    style=None,
                    score=0,
                    reason="It is warm and dry, so an outer layer would be unnecessary.",
                    image_url=None,
                )
            )
            continue
        candidates = [
            item
            for item in wardrobe
            if item["item_type"] == item_type and item.get("laundry_status", "clean") != "laundry"
        ]
        if not candidates:
            continue
        scored = [
            _score_wardrobe_item(
                item,
                selected_items=selected_items,
                rain=rain,
                cold=cold,
                warm=warm,
                has_sport=has_sport,
                has_formal=has_formal,
            )
            for item in candidates
        ]
        ranked = sorted(scored, key=lambda entry: entry[0], reverse=True)
        score, reason, item = ranked[0]
        selected_items.append(item)
        selected.append(_outfit_choice(item, score, reason))

    if has_sport:
        sport_items = [
            _outfit_choice(
                item,
                3,
                "Packed because you have sport today.",
            )
            for item in wardrobe
            if item["sport_ready"] and item["name"] not in [choice.name for choice in selected]
            and item.get("laundry_status", "clean") != "laundry"
        ]
        selected.extend(sport_items[:2])

    return selected


def _score_wardrobe_item(
    item: dict,
    selected_items: list[dict],
    rain: bool,
    cold: bool,
    warm: bool,
    has_sport: bool,
    has_formal: bool,
) -> tuple[int, str, dict]:
    score = 0
    reasons: list[str] = []
    if rain and item["rain_ready"]:
        score += 4
        reasons.append("rain-ready")
    if cold:
        warmth_score = int(item["warmth"]) * 2
        score += warmth_score
        reasons.append(f"warmth {item['warmth']}/5")
    if warm:
        score -= int(item["warmth"])
        if int(item["warmth"]) <= 2:
            score += 2
            reasons.append("light enough for warm weather")

    style = _style_tokens(item)
    if "minimal" in style or "casual" in style:
        score += 1
        reasons.append("campus-friendly style")
    if has_sport and item["sport_ready"]:
        score += 2
        reasons.append("works with sport day")
    if has_formal and item.get("formality") in {"smart", "formal"}:
        score += 3
        reasons.append("fits a formal schedule item")

    color_score = _color_match_score(item, selected_items)
    score += color_score
    if selected_items and color_score > 0:
        reasons.append("matches selected colors")
    elif selected_items and color_score < 0:
        reasons.append("color is less cohesive")

    if item.get("image_url"):
        score += 1
        reasons.append("photo-backed wardrobe item")
    if item.get("laundry_status") == "worn":
        score -= 2
        reasons.append("already worn")
    recent_days = _days_since_worn(item)
    if recent_days is not None and recent_days <= 2:
        score -= 2
        reasons.append("worn recently")

    reason = ", ".join(reasons) if reasons else "best available match"
    return score, reason, item


def _outfit_choice(item: dict, score: int, reason: str) -> OutfitChoice:
    return OutfitChoice(
        name=item["name"],
        item_type=item["item_type"],
        color=item.get("color"),
        style=item.get("style"),
        score=score,
        reason=reason,
        image_url=item.get("image_url"),
    )


def _style_tokens(item: dict) -> set[str]:
    return {token.strip().lower() for token in item.get("style", "").split(",") if token.strip()}


def _days_since_worn(item: dict) -> int | None:
    last_worn_on = item.get("last_worn_on")
    if not last_worn_on:
        return None
    try:
        return (date.today() - date.fromisoformat(last_worn_on)).days
    except ValueError:
        return None


def _color_match_score(item: dict, selected_items: list[dict]) -> int:
    if not selected_items:
        return 0
    color = item.get("color", "").lower()
    selected_colors = {existing.get("color", "").lower() for existing in selected_items}
    if color in NEUTRAL_COLORS:
        return 2
    if any(color in COLOR_FAMILIES.get(existing, set()) for existing in selected_colors):
        return 2
    if any(existing in COLOR_FAMILIES.get(color, set()) for existing in selected_colors):
        return 2
    if selected_colors & NEUTRAL_COLORS:
        return 1
    return -1


def _choose_meal_details(
    groceries: list[dict],
    schedule: list[dict],
    has_sport: bool,
    day: date,
) -> list[MealRecommendation]:
    names = {item["name"].lower() for item in groceries}
    categories = _names_by_category(groceries)
    expiring = _expiring_items(groceries, day)
    protein = _first_matching(names, PROTEIN_PRIORITY) or "eggs"
    carb = _first_matching(names, CARB_PRIORITY) or "rice"
    vegetable = _first_matching(expiring, VEG_PRIORITY) or _first_matching(names, VEG_PRIORITY) or "tomatoes"
    busy_day = len(schedule) >= 3

    if {"oats", "banana", "yogurt"} & names:
        breakfast = MealRecommendation(
            meal="breakfast",
            name="oats with banana and yogurt",
            ingredients=_available_ingredients(names, ["oats", "banana", "yogurt"]),
            prep_minutes=7,
            focus="steady morning energy",
            reason="Fast before university and balanced enough to avoid an early snack run.",
            budget_note="Uses cheap breakfast staples already in your grocery list.",
        )
    elif {"eggs", "egg"} & names and {"bread", "toast"} & names:
        breakfast = MealRecommendation(
            meal="breakfast",
            name="quick eggs and toast",
            ingredients=_available_ingredients(names, ["eggs", "egg", "bread", "toast"]),
            prep_minutes=10,
            focus="simple protein",
            reason="Good when the morning is tight and you still need something filling.",
            budget_note="Eggs are a low-cost protein option.",
        )
    else:
        breakfast = MealRecommendation(
            meal="breakfast",
            name="quick yogurt bowl",
            ingredients=_available_ingredients(names, ["yogurt", "oats", "banana"]) or ["yogurt", "oats"],
            prep_minutes=5,
            focus="minimum-effort breakfast",
            reason="Keeps breakfast realistic when the pantry is light.",
            budget_note="Add missing oats or bananas only if you pass a store.",
        )

    lunch_ingredients = _available_ingredients(names, [carb, vegetable, protein])
    if expiring & names:
        lunch_reason = f"Uses {', '.join(sorted(expiring)[:2])} before it goes bad."
    elif busy_day:
        lunch_reason = "Packable and easy to reheat between university tasks."
    else:
        lunch_reason = "A simple grocery-based meal that keeps lunch cheap."

    lunch = MealRecommendation(
        meal="lunch",
        name=f"{carb} bowl with {vegetable} and {protein}",
        ingredients=lunch_ingredients,
        prep_minutes=18 if busy_day else 20,
        focus="campus fuel",
        reason=lunch_reason,
        budget_note="Prep one extra portion to reduce Mensa or takeaway spending.",
    )

    if has_sport:
        dinner = MealRecommendation(
            meal="dinner",
            name=f"high-protein {protein} {carb} bowl",
            ingredients=_available_ingredients(names, [protein, carb, vegetable]),
            prep_minutes=22,
            focus="post-football recovery",
            reason="Protein supports recovery after sport, while carbs refill energy.",
            budget_note="Uses your existing pantry base instead of buying a separate recovery meal.",
        )
    else:
        dinner_veg = _first_matching(categories.get("vegetable", set()), VEG_PRIORITY) or vegetable
        dinner = MealRecommendation(
            meal="dinner",
            name=f"simple {carb} with {dinner_veg}",
            ingredients=_available_ingredients(names, [carb, dinner_veg, protein]),
            prep_minutes=16,
            focus="light evening meal",
            reason="Easy enough for a study evening and still based on groceries you have.",
            budget_note="Keeps dinner low-cost and avoids duplicate shopping.",
        )

    return [breakfast, lunch, dinner]


def _names_by_category(groceries: list[dict]) -> dict[str, set[str]]:
    categories: dict[str, set[str]] = {}
    for item in groceries:
        category = item.get("category", "other").lower()
        categories.setdefault(category, set()).add(item["name"].lower())
    return categories


def _expiring_items(groceries: list[dict], day: date) -> set[str]:
    expiring: set[str] = set()
    for item in groceries:
        expires_on = item.get("expires_on")
        if not expires_on:
            continue
        try:
            days_left = (date.fromisoformat(expires_on) - day).days
        except ValueError:
            continue
        if 0 <= days_left <= 2:
            expiring.add(item["name"].lower())
    return expiring


def _available_ingredients(names: set[str], candidates: list[str]) -> list[str]:
    ingredients: list[str] = []
    for candidate in candidates:
        if candidate in names and candidate not in ingredients:
            ingredients.append(candidate)
    return ingredients


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
