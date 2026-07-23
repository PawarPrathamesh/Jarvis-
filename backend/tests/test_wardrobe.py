from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import WeatherSummary
from app.services.planner import build_daily_briefing


def test_outfit_skips_laundry_items() -> None:
    weather = WeatherSummary(
        temperature_c=12,
        precipitation_probability=10,
        rain_mm=0,
        wind_kmh=5,
        condition="cloudy",
    )
    wardrobe = [
        {
            "name": "laundry hoodie",
            "item_type": "top",
            "color": "grey",
            "style": "casual",
            "warmth": 5,
            "rain_ready": False,
            "sport_ready": False,
            "formality": "casual",
            "laundry_status": "laundry",
            "last_worn_on": None,
            "image_url": None,
        },
        {
            "name": "clean shirt",
            "item_type": "top",
            "color": "white",
            "style": "casual",
            "warmth": 2,
            "rain_ready": False,
            "sport_ready": False,
            "formality": "casual",
            "laundry_status": "clean",
            "last_worn_on": None,
            "image_url": None,
        },
    ]

    briefing = build_daily_briefing(weather, [], wardrobe, [], date(2026, 7, 24))

    assert "clean shirt" in briefing.outfit
    assert "laundry hoodie" not in briefing.outfit


def test_mark_outfit_worn_endpoint() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/wardrobe",
            json={
                "name": "endpoint test shirt",
                "item_type": "top",
                "color": "blue",
                "style": "casual",
                "warmth": 2,
                "rain_ready": False,
                "sport_ready": False,
                "formality": "casual",
            },
        ).json()

        response = client.post(
            "/wardrobe/mark-outfit-worn",
            json={"item_names": ["endpoint test shirt"], "worn_on": "2026-07-24"},
        )
        updated = client.get("/wardrobe").json()
        item = next(item for item in updated if item["id"] == created["id"])
        client.delete(f"/wardrobe/{created['id']}")

    assert response.status_code == 200
    assert response.json()["updated"] >= 1
    assert item["laundry_status"] == "worn"
    assert item["last_worn_on"] == "2026-07-24"
