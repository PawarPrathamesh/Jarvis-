from datetime import date

from app import repositories
from app.services.shortcuts import build_location_alert


def test_location_alert_near_store(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.shortcuts.list_groceries",
        lambda: [
            {
                "id": 1,
                "name": "chicken",
                "category": "protein",
                "quantity": "500 g",
                "expires_on": "2026-07-24",
                "status": "available",
            }
        ],
    )
    monkeypatch.setattr(
        repositories,
        "list_groceries",
        lambda: [
            {
                "id": 1,
                "name": "chicken",
                "category": "protein",
                "quantity": "500 g",
                "expires_on": "2026-07-24",
                "status": "available",
            }
        ],
    )

    alert = build_location_alert("Aldi Dresden", "arrive", date(2026, 7, 24))

    assert alert["title"] == "Jarvis at Aldi Dresden"
    assert "Aldi Dresden" in alert["message"]
    assert "chicken" in alert["urgent_groceries"]
    assert "Scan receipt after shopping" in alert["actions"]


def test_location_alert_non_store(monkeypatch) -> None:
    monkeypatch.setattr("app.services.shortcuts.list_groceries", lambda: [])
    monkeypatch.setattr(repositories, "list_groceries", lambda: [])

    alert = build_location_alert("TU Dresden", "leave", date(2026, 7, 24))

    assert alert["shopping"] == []
    assert "No store-specific shopping alert" in alert["message"]
