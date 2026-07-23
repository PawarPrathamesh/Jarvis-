import re
from datetime import date, timedelta


CATEGORY_KEYWORDS = {
    "protein": [
        "chicken",
        "haehnchen",
        "hahnchen",
        "egg",
        "eggs",
        "eier",
        "tofu",
        "tuna",
        "thunfisch",
        "lentil",
        "linsen",
        "beans",
        "bohnen",
    ],
    "dairy": ["milk", "milch", "yogurt", "joghurt", "cheese", "kaese", "kase", "quark", "skyr"],
    "carb": [
        "rice",
        "reis",
        "pasta",
        "nudeln",
        "bread",
        "brot",
        "broetchen",
        "brotchen",
        "oats",
        "hafer",
        "potato",
        "kartoffel",
        "wrap",
    ],
    "vegetable": [
        "tomato",
        "tomate",
        "tomaten",
        "spinach",
        "spinat",
        "pepper",
        "paprika",
        "onion",
        "zwiebel",
        "broccoli",
        "brokkoli",
        "salad",
        "salat",
        "gurke",
    ],
    "fruit": ["banana", "banane", "bananen", "apple", "apfel", "aepfel", "apfel", "orange", "berries", "beeren", "trauben"],
    "snack": ["chips", "chocolate", "schokolade", "cookie", "keks", "biscuit", "snack", "riegel"],
    "drink": ["cola", "juice", "saft", "water", "wasser", "beer", "bier", "coffee", "kaffee"],
    "household": ["soap", "seife", "detergent", "waschmittel", "paper", "papier", "tissue", "kuechenrolle", "toilettenpapier"],
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
    lowered = _ascii_german(name.lower())
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other"


def _parse_line(line: str) -> dict | None:
    cleaned = _normalize_ocr_text(line)
    if not cleaned or _looks_like_total(cleaned):
        return None

    match = re.match(
        r"^(?P<name>.+?)\s+(?P<price>\d+[,.]\d{2})\s*(?:[AB]\s*)?(?:EUR|€)?$",
        cleaned,
        re.IGNORECASE,
    )
    if not match:
        return None

    name = _clean_name(match.group("name"))
    if not name or _looks_like_total(name):
        return None

    price = float(match.group("price").replace(",", "."))
    return {
        "name": name,
        "category": categorize_item(name),
        "quantity": _extract_quantity(cleaned),
        "price": price,
    }


def _looks_like_total(line: str) -> bool:
    lowered = _ascii_german(line.lower())
    total_words = [
        "total",
        "summe",
        "zwischensumme",
        "betrag",
        "bon",
        "datum",
        "filiale",
        "steuer",
        "ust",
        "mwst",
        "visa",
        "mastercard",
        "gegeben",
        "rueckgeld",
        "kartenzahlung",
    ]
    return any(word in lowered for word in total_words)


def _clean_name(name: str) -> str:
    cleaned = _normalize_ocr_text(name)
    cleaned = re.sub(r"\b\d{8,14}\b", "", cleaned)
    cleaned = re.sub(
        r"\b\d+[,.]\d{1,3}\s*(?:kg|g|l|ml)\s*x\s*\d+[,.]\d{2}\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"^\d+\s*x\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bpfand\b", "deposit", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+[AB]$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -*#")
    return cleaned.lower()


def _extract_quantity(line: str) -> str:
    lowered = _ascii_german(line.lower())
    weighted = re.search(
        r"(?P<amount>\d+[,.]\d{1,3})\s*(?P<unit>kg|g|l|ml)\s*x\s*(?P<unit_price>\d+[,.]\d{2})",
        lowered,
    )
    if weighted:
        amount = weighted.group("amount").replace(",", ".")
        return f"{amount} {weighted.group('unit')}"

    count = re.search(r"(?P<count>\d+)\s*x\s+", lowered)
    if count:
        return f"{count.group('count')} items"

    pieces = re.search(r"\b(?P<count>\d+)\s*(st|stk|stueck)\b", lowered)
    if pieces:
        return f"{pieces.group('count')} items"

    return "1 item"


def _normalize_ocr_text(line: str) -> str:
    cleaned = line.strip()
    replacements = {
        "â‚¬": "€",
        "Ã¼": "ü",
        "Ãœ": "Ü",
        "Ã¤": "ä",
        "Ã„": "Ä",
        "Ã¶": "ö",
        "Ã–": "Ö",
        "ÃŸ": "ß",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    return re.sub(r"\s+", " ", cleaned)


def _ascii_german(value: str) -> str:
    return (
        value.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
