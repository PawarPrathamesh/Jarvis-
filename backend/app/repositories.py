from datetime import date, datetime

from app.database import get_connection
from app.services.receipts import estimate_expiry


DEFAULT_BUDGETS = {
    "monthly_food_budget": 250.0,
    "monthly_snack_budget": 25.0,
    "monthly_eating_out_budget": 60.0,
}


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


def grocery_expiry_summary(day: date) -> dict:
    buckets = {
        "expired": [],
        "today": [],
        "soon": [],
        "later": [],
        "unknown": [],
    }
    for item in list_groceries():
        expires_on = item.get("expires_on")
        if not expires_on:
            buckets["unknown"].append(_expiry_item(item, None, "unknown"))
            continue
        try:
            days_left = (date.fromisoformat(expires_on) - day).days
        except ValueError:
            buckets["unknown"].append(_expiry_item(item, None, "unknown"))
            continue

        if days_left < 0:
            buckets["expired"].append(_expiry_item(item, days_left, "expired"))
        elif days_left == 0:
            buckets["today"].append(_expiry_item(item, days_left, "today"))
        elif days_left <= 3:
            buckets["soon"].append(_expiry_item(item, days_left, "soon"))
        else:
            buckets["later"].append(_expiry_item(item, days_left, "later"))

    return {
        **buckets,
        "suggestions": _expiry_suggestions(buckets),
    }


def _expiry_item(item: dict, days_left: int | None, urgency: str) -> dict:
    return {
        "id": item["id"],
        "name": item["name"],
        "category": item["category"],
        "quantity": item["quantity"],
        "expires_on": item.get("expires_on"),
        "days_left": days_left,
        "urgency": urgency,
    }


def _expiry_suggestions(buckets: dict[str, list[dict]]) -> list[str]:
    suggestions: list[str] = []
    priority = buckets["expired"] + buckets["today"] + buckets["soon"]
    if priority:
        names = ", ".join(item["name"] for item in priority[:4])
        suggestions.append(f"Use these first: {names}.")
    if buckets["unknown"]:
        suggestions.append("Add expiry dates to groceries with unknown shelf life for better meal planning.")
    if not suggestions:
        suggestions.append("Pantry looks calm. Keep using older groceries first.")
    return suggestions


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


def delete_grocery(grocery_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE groceries
            SET status = 'deleted'
            WHERE id = ?
            """,
            (grocery_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Grocery not found: {grocery_id}")


def list_wardrobe_items() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, item_type, color, style, warmth, rain_ready,
                   sport_ready, formality, laundry_status, last_worn_on, status, image_path
            FROM wardrobe_items
            WHERE status = 'available'
            ORDER BY item_type, name
            """
        ).fetchall()
    return [_with_image_url(dict(row)) for row in rows]


def create_wardrobe_item(payload: dict) -> dict:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO wardrobe_items
            (name, item_type, color, style, warmth, rain_ready, sport_ready, formality,
             laundry_status, last_worn_on, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                payload.get("laundry_status", "clean"),
                payload.get("last_worn_on"),
                payload.get("image_path"),
            ),
        )
        row = connection.execute(
            """
            SELECT id, name, item_type, color, style, warmth, rain_ready,
                   sport_ready, formality, laundry_status, last_worn_on, status, image_path
            FROM wardrobe_items
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return _with_image_url(dict(row))


def update_wardrobe_item(item_id: int, payload: dict) -> dict:
    allowed_statuses = {"clean", "worn", "laundry"}
    updates: list[str] = []
    values: list[str | int | None] = []
    if "laundry_status" in payload and payload["laundry_status"] is not None:
        laundry_status = payload["laundry_status"]
        if laundry_status not in allowed_statuses:
            raise ValueError("Unsupported laundry status")
        updates.append("laundry_status = ?")
        values.append(laundry_status)
    if "last_worn_on" in payload:
        updates.append("last_worn_on = ?")
        values.append(payload["last_worn_on"])
    if not updates:
        return _get_wardrobe_item(item_id)

    values.append(item_id)
    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE wardrobe_items
            SET {', '.join(updates)}
            WHERE id = ? AND status = 'available'
            """,
            tuple(values),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Wardrobe item not found: {item_id}")
    return _get_wardrobe_item(item_id)


def mark_outfit_worn(item_names: list[str], worn_on: date) -> dict:
    filtered_names = [name for name in item_names if name and not name.startswith("no jacket")]
    if not filtered_names:
        return {"updated": 0, "worn_on": worn_on.isoformat()}
    placeholders = ",".join("?" for _ in filtered_names)
    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE wardrobe_items
            SET laundry_status = 'worn', last_worn_on = ?
            WHERE name IN ({placeholders}) AND status = 'available'
            """,
            (worn_on.isoformat(), *filtered_names),
        )
    return {"updated": cursor.rowcount, "worn_on": worn_on.isoformat()}


def _get_wardrobe_item(item_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, item_type, color, style, warmth, rain_ready,
                   sport_ready, formality, laundry_status, last_worn_on, status, image_path
            FROM wardrobe_items
            WHERE id = ? AND status = 'available'
            """,
            (item_id,),
        ).fetchone()
    if row is None:
        raise ValueError(f"Wardrobe item not found: {item_id}")
    return _with_image_url(dict(row))


def delete_wardrobe_item(item_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE wardrobe_items
            SET status = 'deleted'
            WHERE id = ?
            """,
            (item_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Wardrobe item not found: {item_id}")


def list_schedule_for_day(day: date) -> list[dict]:
    day_prefix = day.isoformat()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, starts_at, ends_at, location, activity_type, near_store,
                   external_id, source
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
            (title, starts_at, ends_at, location, activity_type, near_store, external_id, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["starts_at"],
                payload["ends_at"],
                payload.get("location"),
                payload.get("activity_type", "lecture"),
                payload.get("near_store"),
                payload.get("external_id"),
                payload.get("source"),
            ),
        )
        row = connection.execute(
            """
            SELECT id, title, starts_at, ends_at, location, activity_type, near_store,
                   external_id, source
            FROM schedule_items
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def delete_schedule_item(schedule_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM schedule_items
            WHERE id = ?
            """,
            (schedule_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Schedule item not found: {schedule_id}")


def import_schedule_events(events: list[dict]) -> dict:
    imported = 0
    updated = 0
    skipped = 0
    with get_connection() as connection:
        for event in events:
            existing = None
            if event.get("external_id"):
                existing = connection.execute(
                    """
                    SELECT id
                    FROM schedule_items
                    WHERE external_id = ? AND source = ?
                    """,
                    (event["external_id"], event.get("source", "apple_calendar")),
                ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE schedule_items
                    SET title = ?, starts_at = ?, ends_at = ?, location = ?,
                        activity_type = ?, near_store = ?
                    WHERE id = ?
                    """,
                    (
                        event["title"],
                        event["starts_at"],
                        event["ends_at"],
                        event.get("location"),
                        event.get("activity_type", "event"),
                        event.get("near_store"),
                        existing["id"],
                    ),
                )
                updated += 1
                continue

            connection.execute(
                """
                INSERT INTO schedule_items
                (title, starts_at, ends_at, location, activity_type, near_store, external_id, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["title"],
                    event["starts_at"],
                    event["ends_at"],
                    event.get("location"),
                    event.get("activity_type", "event"),
                    event.get("near_store"),
                    event.get("external_id"),
                    event.get("source", "apple_calendar"),
                ),
            )
            imported += 1
    return {"imported": imported, "updated": updated, "skipped": skipped, "source": "apple_calendar"}


def list_calendar_sources() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, source_type, value, active, last_synced_at
            FROM calendar_sources
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_active_calendar_sources() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, source_type, value, active, last_synced_at
            FROM calendar_sources
            WHERE active = 1
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_calendar_source(payload: dict) -> dict:
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT id
            FROM calendar_sources
            WHERE source_type = ? AND value = ?
            """,
            (payload.get("source_type", "file"), payload["value"]),
        ).fetchone()
        if existing:
            connection.execute(
                """
                UPDATE calendar_sources
                SET name = ?, active = 1
                WHERE id = ?
                """,
                (payload["name"], existing["id"]),
            )
            source_id = existing["id"]
        else:
            cursor = connection.execute(
                """
                INSERT INTO calendar_sources (name, source_type, value)
                VALUES (?, ?, ?)
                """,
                (payload["name"], payload.get("source_type", "file"), payload["value"]),
            )
            source_id = cursor.lastrowid

        row = connection.execute(
            """
            SELECT id, name, source_type, value, active, last_synced_at
            FROM calendar_sources
            WHERE id = ?
            """,
            (source_id,),
        ).fetchone()
    return dict(row)


def mark_calendar_source_synced(source_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE calendar_sources
            SET last_synced_at = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(timespec="seconds"), source_id),
        )


def delete_calendar_source(source_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE calendar_sources
            SET active = 0
            WHERE id = ?
            """,
            (source_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Calendar source not found: {source_id}")


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
    result["image_url"] = _receipt_image_url(result.get("image_path"))
    return result


def delete_receipt(receipt_id: int) -> None:
    get_receipt(receipt_id)
    with get_connection() as connection:
        connection.execute("DELETE FROM receipt_items WHERE receipt_id = ?", (receipt_id,))
        connection.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))


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


def get_budget_settings() -> dict:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT key, value
            FROM preferences
            WHERE key IN (?, ?, ?)
            """,
            tuple(DEFAULT_BUDGETS.keys()),
        ).fetchall()

    values = DEFAULT_BUDGETS.copy()
    for row in rows:
        values[row["key"]] = float(row["value"])
    return values


def update_budget_settings(payload: dict) -> dict:
    values = DEFAULT_BUDGETS.copy()
    values.update({key: float(value) for key, value in payload.items()})
    with get_connection() as connection:
        for key, value in values.items():
            connection.execute(
                """
                INSERT INTO preferences (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, str(value)),
            )
    return get_budget_settings()


def monthly_budget_status(month: str) -> dict:
    settings = get_budget_settings()
    summary = monthly_expense_summary(month)
    budget = settings["monthly_food_budget"]
    spent = summary["total"]
    remaining = round(budget - spent, 2)
    percent_used = round((spent / budget) * 100, 1) if budget else 0

    if percent_used >= 100:
        status = "over_budget"
        message = "You are over your monthly food budget. Prefer pantry meals and avoid impulse shopping."
    elif percent_used >= 85:
        status = "near_limit"
        message = "You are close to your monthly food budget. Keep the next shopping trip focused."
    else:
        status = "on_track"
        message = "You are on track with your monthly food budget."

    return {
        "month": month,
        "monthly_food_budget": budget,
        "spent": spent,
        "remaining": remaining,
        "percent_used": percent_used,
        "status": status,
        "message": message,
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


def _with_image_url(item: dict) -> dict:
    image_path = item.get("image_path")
    item["image_url"] = f"/uploads/{image_path}" if image_path else None
    return item


def _receipt_image_url(image_path: str | None) -> str | None:
    if not image_path:
        return None
    normalized = image_path.replace("\\", "/")
    if "/uploads/" in normalized:
        return f"/uploads/{normalized.split('/uploads/', 1)[1]}"
    return f"/uploads/{normalized}"
