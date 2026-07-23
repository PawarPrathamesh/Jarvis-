from datetime import date

from app.services.receipts import categorize_item, estimate_expiry, parse_receipt_text


def test_parse_german_weighted_receipt_line() -> None:
    items = parse_receipt_text("BANANEN 0,742 kg x 1,79 1,33\nSUMME 1,33")

    assert items == [
        {
            "name": "bananen",
            "category": "fruit",
            "quantity": "0.742 kg",
            "price": 1.33,
        }
    ]


def test_parse_german_tax_suffix_and_count() -> None:
    items = parse_receipt_text("2 x MILCH 2,38 A\nBIO EIER 10 St 3,49 B\nKARTENZAHLUNG 5,87")

    assert items[0]["name"] == "milch"
    assert items[0]["category"] == "dairy"
    assert items[0]["quantity"] == "2 items"
    assert items[1]["name"] == "bio eier 10 st"
    assert items[1]["category"] == "protein"
    assert items[1]["quantity"] == "10 items"


def test_categorize_and_expiry_estimate() -> None:
    assert categorize_item("Haferflocken") == "carb"
    assert categorize_item("Paprika Mix") == "vegetable"
    assert estimate_expiry("dairy", date(2026, 7, 23)) == "2026-07-28"
