from datetime import date

from app import repositories


def test_grocery_expiry_summary_buckets(monkeypatch) -> None:
    monkeypatch.setattr(
        repositories,
        "list_groceries",
        lambda: [
            {
                "id": 1,
                "name": "milk",
                "category": "dairy",
                "quantity": "1 bottle",
                "expires_on": "2026-07-23",
            },
            {
                "id": 2,
                "name": "spinach",
                "category": "vegetable",
                "quantity": "1 bag",
                "expires_on": "2026-07-25",
            },
            {
                "id": 3,
                "name": "rice",
                "category": "carb",
                "quantity": "1 kg",
                "expires_on": None,
            },
        ],
    )

    summary = repositories.grocery_expiry_summary(date(2026, 7, 23))

    assert [item["name"] for item in summary["today"]] == ["milk"]
    assert [item["name"] for item in summary["soon"]] == ["spinach"]
    assert [item["name"] for item in summary["unknown"]] == ["rice"]
    assert summary["suggestions"][0] == "Use these first: milk, spinach."
