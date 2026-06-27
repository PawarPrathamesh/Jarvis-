from datetime import date

from app.database import get_connection


def list_groceries() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, category, quantity, expires_on, store, price, status
            FROM groceries
            WHERE status = 'available'
            ORDER BY expires_on IS NULL, expires_on ASC, name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_grocery(payload: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO groceries (name, category, quantity, expires_on, store, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["name"],
                payload["category"],
                payload["quantity"],
                payload.get("expires_on"),
                payload.get("store"),
                payload.get("price"),
            ),
        )
        row = connection.execute(
            """
            SELECT id, name, category, quantity, expires_on, store, price, status
            FROM groceries
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_wardrobe_items() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, item_type, color, style, warmth, rain_ready,
                   sport_ready, formality, status
            FROM wardrobe_items
            WHERE status = 'available'
            ORDER BY item_type, name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_wardrobe_item(payload: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO wardrobe_items
            (name, item_type, color, style, warmth, rain_ready, sport_ready, formality)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["name"],
                payload["item_type"],
                payload["color"],
                payload["style"],
                payload.get("warmth", 1),
                int(payload.get("rain_ready", False)),
                int(payload.get("sport_ready", False)),
                payload.get("formality", "casual"),
            ),
        )
        row = connection.execute(
            """
            SELECT id, name, item_type, color, style, warmth, rain_ready,
                   sport_ready, formality, status
            FROM wardrobe_items
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_schedule_for_day(day: date) -> list[dict]:
    day_prefix = day.isoformat()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, starts_at, ends_at, location, activity_type, near_store
            FROM schedule_items
            WHERE starts_at LIKE ?
            ORDER BY starts_at ASC
            """,
            (f"{day_prefix}%",),
        ).fetchall()
    return [dict(row) for row in rows]


def create_schedule_item(payload: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO schedule_items
            (title, starts_at, ends_at, location, activity_type, near_store)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["starts_at"],
                payload["ends_at"],
                payload.get("location"),
                payload.get("activity_type", "lecture"),
                payload.get("near_store"),
            ),
        )
        row = connection.execute(
            """
            SELECT id, title, starts_at, ends_at, location, activity_type, near_store
            FROM schedule_items
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)
