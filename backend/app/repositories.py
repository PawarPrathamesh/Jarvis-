from datetime import date

from app.database import get_connection
from app.services.receipts import estimate_expiry


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


def create_receipt_from_items(
    store: str,
    purchased_on: date,
    raw_text: str | None,
    items: list[dict],
    image_path: str | None = None,
    status: str = "processed",
) -> dict:
    total = round(sum(float(item.get("price") or 0) for item in items), 2)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO receipts (store, purchased_on, total, image_path, raw_text, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (store, purchased_on.isoformat(), total, image_path, raw_text, status),
        )
        receipt_id = cursor.lastrowid

        for item in items:
            category = item["category"]
            connection.execute(
                """
                INSERT INTO receipt_items
                (receipt_id, name, category, quantity, price, inventory_added)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    item["name"],
                    category,
                    item.get("quantity", "1 item"),
                    item.get("price", 0),
                    int(category not in {"snack", "drink", "household", "other"}),
                ),
            )
            if category not in {"snack", "drink", "household", "other"}:
                connection.execute(
                    """
                    INSERT INTO groceries (name, category, quantity, expires_on, store, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["name"],
                        category,
                        item.get("quantity", "1 item"),
                        estimate_expiry(category, purchased_on),
                        store,
                        item.get("price", 0),
                    ),
                )

    return get_receipt(receipt_id)


def process_existing_receipt_text(receipt_id: int, raw_text: str, items: list[dict]) -> dict:
    receipt = get_receipt(receipt_id)
    purchased_on = date.fromisoformat(receipt["purchased_on"])
    total = round(sum(float(item.get("price") or 0) for item in items), 2)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE receipts
            SET raw_text = ?, total = ?, status = 'processed'
            WHERE id = ?
            """,
            (raw_text, total, receipt_id),
        )
        connection.execute("DELETE FROM receipt_items WHERE receipt_id = ?", (receipt_id,))

        for item in items:
            category = item["category"]
            inventory_added = category not in {"snack", "drink", "household", "other"}
            connection.execute(
                """
                INSERT INTO receipt_items
                (receipt_id, name, category, quantity, price, inventory_added)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    item["name"],
                    category,
                    item.get("quantity", "1 item"),
                    item.get("price", 0),
                    int(inventory_added),
                ),
            )
            if inventory_added:
                connection.execute(
                    """
                    INSERT INTO groceries (name, category, quantity, expires_on, store, price)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["name"],
                        category,
                        item.get("quantity", "1 item"),
                        estimate_expiry(category, purchased_on),
                        receipt["store"],
                        item.get("price", 0),
                    ),
                )

    return get_receipt(receipt_id)


def list_receipts() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, store, purchased_on, total, image_path, raw_text, status
            FROM receipts
            ORDER BY purchased_on DESC, id DESC
            """
        ).fetchall()
    return [get_receipt(row["id"]) for row in rows]


def get_receipt(receipt_id: int) -> dict:
    with get_connection() as connection:
        receipt = connection.execute(
            """
            SELECT id, store, purchased_on, total, image_path, raw_text, status
            FROM receipts
            WHERE id = ?
            """,
            (receipt_id,),
        ).fetchone()
        if receipt is None:
            raise ValueError(f"Receipt not found: {receipt_id}")
        items = connection.execute(
            """
            SELECT id, receipt_id, name, category, quantity, price, inventory_added
            FROM receipt_items
            WHERE receipt_id = ?
            ORDER BY id
            """,
            (receipt_id,),
        ).fetchall()
    result = dict(receipt)
    result["items"] = [dict(item) for item in items]
    return result


def monthly_expense_summary(month: str) -> dict:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT receipt_items.category,
                   ROUND(SUM(receipt_items.price), 2) AS total,
                   COUNT(*) AS item_count
            FROM receipt_items
            JOIN receipts ON receipts.id = receipt_items.receipt_id
            WHERE receipts.purchased_on LIKE ?
            GROUP BY receipt_items.category
            ORDER BY total DESC
            """,
            (f"{month}-%",),
        ).fetchall()

    categories = [dict(row) for row in rows]
    total = round(sum(row["total"] for row in categories), 2)
    return {
        "month": month,
        "total": total,
        "categories": categories,
        "suggestions": _saving_suggestions(categories),
    }


def _saving_suggestions(categories: list[dict]) -> list[str]:
    totals = {row["category"]: row["total"] for row in categories}
    suggestions: list[str] = []
    if totals.get("snack", 0) >= 15:
        suggestions.append("Snack spending is high; replace some snacks with fruit, oats, or yogurt.")
    if totals.get("drink", 0) >= 15:
        suggestions.append("Drink spending is high; carry water from home on lecture days.")
    if totals.get("protein", 0) >= 40:
        suggestions.append("Compare protein prices and batch-cook chicken, lentils, or eggs.")
    if not suggestions and categories:
        suggestions.append("Spending looks balanced. Keep using groceries before they expire.")
    if not categories:
        suggestions.append("No receipt spending tracked for this month yet.")
    return suggestions
