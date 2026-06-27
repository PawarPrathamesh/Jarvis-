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


class ScheduleItem(ScheduleItemCreate):
    id: int


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
