import sqlite3
from collections.abc import Iterator

from app.config import DATA_DIR, DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def iter_rows(query: str, params: tuple = ()) -> Iterator[sqlite3.Row]:
    with get_connection() as connection:
        yield from connection.execute(query, params).fetchall()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS groceries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity TEXT NOT NULL,
                expires_on TEXT,
                store TEXT,
                price REAL,
                status TEXT NOT NULL DEFAULT 'available'
            );

            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                color TEXT NOT NULL,
                style TEXT NOT NULL,
                warmth INTEGER NOT NULL DEFAULT 1,
                rain_ready INTEGER NOT NULL DEFAULT 0,
                sport_ready INTEGER NOT NULL DEFAULT 0,
                formality TEXT NOT NULL DEFAULT 'casual',
                status TEXT NOT NULL DEFAULT 'available'
            );

            CREATE TABLE IF NOT EXISTS schedule_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                location TEXT,
                activity_type TEXT NOT NULL DEFAULT 'lecture',
                near_store TEXT
            );

            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store TEXT NOT NULL,
                purchased_on TEXT NOT NULL,
                total REAL NOT NULL DEFAULT 0,
                image_path TEXT,
                raw_text TEXT,
                status TEXT NOT NULL DEFAULT 'processed',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity TEXT NOT NULL DEFAULT '1 item',
                price REAL NOT NULL DEFAULT 0,
                inventory_added INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (receipt_id) REFERENCES receipts(id)
            );
            """
        )
        _ensure_column(connection, "wardrobe_items", "image_path", "TEXT")
        _ensure_column(connection, "schedule_items", "external_id", "TEXT")
        _ensure_column(connection, "schedule_items", "source", "TEXT")


def _ensure_column(
    connection: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = [row["name"] for row in connection.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
