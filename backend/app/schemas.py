from pydantic import BaseModel


class GroceryCreate(BaseModel):
    name: str
    category: str
    quantity: str
    expires_on: str | None = None
    store: str | None = None
    price: float | None = None


class Grocery(GroceryCreate):
    id: int
    status: str


class WardrobeItemCreate(BaseModel):
    name: str
    item_type: str
    color: str
    style: str
    warmth: int = 1
    rain_ready: bool = False
    sport_ready: bool = False
    formality: str = "casual"
    image_path: str | None = None
    image_url: str | None = None


class WardrobeItem(WardrobeItemCreate):
    id: int
    status: str


class ScheduleItemCreate(BaseModel):
    title: str
    starts_at: str
    ends_at: str
    location: str | None = None
    activity_type: str = "lecture"
    near_store: str | None = None
    external_id: str | None = None
    source: str | None = None


class ScheduleItem(ScheduleItemCreate):
    id: int


class CalendarImportUrl(BaseModel):
    url: str


class CalendarImportText(BaseModel):
    raw_ics: str


class CalendarImportResult(BaseModel):
    imported: int
    skipped: int
    source: str = "apple_calendar"


class ReceiptTextCreate(BaseModel):
    store: str
    purchased_on: str
    raw_text: str


class ReceiptProcessText(BaseModel):
    raw_text: str


class OcrStatus(BaseModel):
    available: bool
    message: str


class ReceiptItem(BaseModel):
    id: int
    receipt_id: int
    name: str
    category: str
    quantity: str
    price: float
    inventory_added: bool


class Receipt(BaseModel):
    id: int
    store: str
    purchased_on: str
    total: float
    image_path: str | None = None
    raw_text: str | None = None
    status: str
    items: list[ReceiptItem] = []


class ExpenseCategorySummary(BaseModel):
    category: str
    total: float
    item_count: int


class MonthlyExpenseSummary(BaseModel):
    month: str
    total: float
    categories: list[ExpenseCategorySummary]
    suggestions: list[str]


class BudgetSettings(BaseModel):
    monthly_food_budget: float = 250.0
    monthly_snack_budget: float = 25.0
    monthly_eating_out_budget: float = 60.0


class BudgetStatus(BaseModel):
    month: str
    monthly_food_budget: float
    spent: float
    remaining: float
    percent_used: float
    status: str
    message: str


class WeatherSummary(BaseModel):
    temperature_c: float
    feels_like_c: float | None = None
    precipitation_probability: int
    rain_mm: float
    wind_kmh: float
    condition: str


class DailyBriefing(BaseModel):
    greeting: str
    weather: WeatherSummary
    schedule: list[str]
    outfit: list[str]
    meals: dict[str, str]
    shopping: list[str]
    alerts: list[str]
