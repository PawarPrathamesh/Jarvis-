from datetime import date, datetime, time, timedelta

from app.database import get_connection, initialize_database


def seed() -> None:
    initialize_database()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    groceries = [
        ("eggs", "protein", "10 pieces", None, "Aldi", 2.49),
        ("rice", "carb", "1 kg", None, "Aldi", 1.99),
        ("chicken", "protein", "500 g", tomorrow.isoformat(), "Aldi", 4.99),
        ("yogurt", "protein", "500 g", (today + timedelta(days=4)).isoformat(), "Aldi", 1.29),
        ("tomatoes", "vegetable", "4 pieces", (today + timedelta(days=2)).isoformat(), "Aldi", 1.89),
        ("oats", "carb", "500 g", None, "Aldi", 0.99),
        ("banana", "fruit", "5 pieces", (today + timedelta(days=3)).isoformat(), "Aldi", 1.39),
    ]

    wardrobe = [
        ("black waterproof jacket", "jacket", "black", "minimal,casual", 4, 1, 0, "casual"),
        ("grey hoodie", "top", "grey", "casual,streetwear", 3, 0, 0, "casual"),
        ("white t-shirt", "top", "white", "minimal,casual", 1, 0, 0, "casual"),
        ("dark jeans", "bottom", "dark blue", "minimal,casual", 2, 0, 0, "casual"),
        ("black joggers", "bottom", "black", "sport,casual", 2, 0, 1, "casual"),
        ("white sneakers", "shoes", "white", "minimal,casual", 1, 0, 0, "casual"),
        ("running shoes", "shoes", "black", "sport", 1, 1, 1, "sport"),
        ("football kit", "sport", "blue", "sport", 1, 0, 1, "sport"),
    ]

    starts_lecture = datetime.combine(today, time(10, 0))
    ends_lecture = datetime.combine(today, time(12, 0))
    starts_football = datetime.combine(today, time(18, 30))
    ends_football = datetime.combine(today, time(20, 0))

    schedule = [
        ("Machine Learning lecture", starts_lecture.isoformat(), ends_lecture.isoformat(), "TU Dresden", "lecture", "Aldi"),
        ("Football", starts_football.isoformat(), ends_football.isoformat(), "Sports field", "football", None),
    ]

    with get_connection() as connection:
        connection.execute("DELETE FROM groceries")
        connection.execute("DELETE FROM wardrobe_items")
        connection.execute("DELETE FROM schedule_items")
        connection.executemany(
            """
            INSERT INTO groceries (name, category, quantity, expires_on, store, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            groceries,
        )
        connection.executemany(
            """
            INSERT INTO wardrobe_items
            (name, item_type, color, style, warmth, rain_ready, sport_ready, formality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            wardrobe,
        )
        connection.executemany(
            """
            INSERT INTO schedule_items
            (title, starts_at, ends_at, location, activity_type, near_store)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            schedule,
        )


if __name__ == "__main__":
    seed()
    print("Seeded Jarvis sample data.")

