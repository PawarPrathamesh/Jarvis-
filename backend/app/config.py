from pathlib import Path
from os import getenv

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "jarvis.db"
UPLOADS_DIR = BASE_DIR / "uploads"
WARDROBE_UPLOADS_DIR = UPLOADS_DIR / "wardrobe"
RECEIPT_UPLOADS_DIR = UPLOADS_DIR / "receipts"

DRESDEN_LATITUDE = 51.0504
DRESDEN_LONGITUDE = 13.7373
DEFAULT_TIMEZONE = "Europe/Berlin"

APPLE_CALDAV_BASE_URL = getenv("APPLE_CALDAV_BASE_URL", "https://caldav.icloud.com")
APPLE_CALDAV_USERNAME = getenv("APPLE_CALDAV_USERNAME")
APPLE_CALDAV_PASSWORD = getenv("APPLE_CALDAV_PASSWORD")
APPLE_CALDAV_CALENDAR_NAME = getenv("APPLE_CALDAV_CALENDAR_NAME")

OPENAI_API_KEY = getenv("OPENAI_API_KEY")
OPENAI_MODEL = getenv("OPENAI_MODEL", "gpt-5-mini")
OPENAI_BASE_URL = getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
