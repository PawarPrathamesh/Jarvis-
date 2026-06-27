from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "jarvis.db"
UPLOADS_DIR = BASE_DIR / "uploads"

DRESDEN_LATITUDE = 51.0504
DRESDEN_LONGITUDE = 13.7373
DEFAULT_TIMEZONE = "Europe/Berlin"
