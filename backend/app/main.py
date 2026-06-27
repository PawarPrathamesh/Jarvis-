from datetime import date

from fastapi import FastAPI

from app.database import initialize_database
from app.repositories import (
    create_grocery,
    create_schedule_item,
    create_wardrobe_item,
    list_groceries,
    list_schedule_for_day,
    list_wardrobe_items,
)
from app.schemas import (
    DailyBriefing,
    Grocery,
    GroceryCreate,
    ScheduleItem,
    ScheduleItemCreate,
    WardrobeItem,
    WardrobeItemCreate,
)
from app.services.planner import build_daily_briefing
from app.services.weather import get_dresden_weather


app = FastAPI(title="Jarvis Student Agent", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "Jarvis"}


@app.get("/daily-briefing", response_model=DailyBriefing)
async def daily_briefing(day: date | None = None) -> DailyBriefing:
    target_day = day or date.today()
    weather = await get_dresden_weather()
    groceries = list_groceries()
    wardrobe = list_wardrobe_items()
    schedule = list_schedule_for_day(target_day)
    return build_daily_briefing(weather, groceries, wardrobe, schedule, target_day)


@app.get("/groceries", response_model=list[Grocery])
def groceries() -> list[dict]:
    return list_groceries()


@app.post("/groceries", response_model=Grocery, status_code=201)
def add_grocery(payload: GroceryCreate) -> dict:
    return create_grocery(payload.model_dump())


@app.get("/wardrobe", response_model=list[WardrobeItem])
def wardrobe() -> list[dict]:
    return list_wardrobe_items()


@app.post("/wardrobe", response_model=WardrobeItem, status_code=201)
def add_wardrobe_item(payload: WardrobeItemCreate) -> dict:
    return create_wardrobe_item(payload.model_dump())


@app.get("/schedule", response_model=list[ScheduleItem])
def schedule(day: date | None = None) -> list[dict]:
    return list_schedule_for_day(day or date.today())


@app.post("/schedule", response_model=ScheduleItem, status_code=201)
def add_schedule_item(payload: ScheduleItemCreate) -> dict:
    return create_schedule_item(payload.model_dump())
