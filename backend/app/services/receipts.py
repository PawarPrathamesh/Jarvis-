import re
from datetime import date, timedelta


CATEGORY_KEYWORDS = {
    "protein": ["chicken", "egg", "eggs", "tofu", "tuna", "lentil", "beans"],
    "dairy": ["milk", "yogurt", "cheese", "quark"],
    "carb": ["rice", "pasta", "bread", "oats", "potato", "wrap"],
    "vegetable": ["tomato", "spinach", "pepper", "onion", "broccoli", "salad"],
    "fruit": ["banana", "apple", "orange", "berries"],
    "snack": ["chips", "chocolate", "cookie", "biscuit", "snack"],
    "drink": ["cola", "juice", "water", "beer", "coffee"],
    "household": ["soap", "detergent", "paper", "tissue"],
}

EXPIRY_DAYS_BY_CATEGORY = {
    "protein": 2,
    "dairy": 5,
    "vegetable": 4,
    "fruit": 5,
    "carb": 180,
}


def parse_receipt_text(raw_text: str) -> list[dict]:
    items: list[dict] = []
    for line in raw_text.splitlines():
        parsed = _parse_line(line)
        if parsed:
            items.append(parsed)
    return items


def estimate_expiry(category: str, purchased_on: date) -> str | None:
    days = EXPIRY_DAYS_BY_CATEGORY.get(category)
    if not days:
        return None
    return (purchased_on + timedelta(days=days)).isoformat()


def categorize_item(name: str) -> str:
    lowered = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other"


def _parse_line(line: str) -> dict | None:
    cleaned = line.strip()
    if not cleaned:
        return None
    if _looks_like_total(cleaned):
        return None

    match = re.match(r"^(?P<name>.+?)\s+(?P<price>\d+[,.]\d{2})\s*(?:EUR|€)?$", cleaned, re.IGNORECASE)
    if not match:
        return None

    name = _clean_name(match.group("name"))
    if not name:
        return None

    price = float(match.group("price").replace(",", "."))
    return {
        "name": name,
        "category": categorize_item(name),
        "quantity": "1 item",
        "price": price,
    }


def _looks_like_total(line: str) -> bool:
    lowered = line.lower()
    total_words = ["total", "summe", "betrag", "visa", "mastercard", "gegeben", "rückgeld"]
    return any(word in lowered for word in total_words)


def _clean_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name).strip(" -*#")
    cleaned = re.sub(r"^\d+\s*x\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned.lower()
