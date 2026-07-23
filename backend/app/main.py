from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import RECEIPT_UPLOADS_DIR, UPLOADS_DIR, WARDROBE_UPLOADS_DIR
from app.config import APPLE_CALDAV_PASSWORD, APPLE_CALDAV_USERNAME
from app.database import initialize_database
from app.repositories import (
    create_grocery,
    create_calendar_source,
    create_receipt_from_items,
    create_schedule_item,
    create_wardrobe_item,
    delete_calendar_source,
    delete_grocery,
    delete_receipt,
    delete_schedule_item,
    delete_wardrobe_item,
    get_budget_settings,
    grocery_expiry_summary,
    import_schedule_events,
    list_calendar_sources,
    list_receipts,
    list_groceries,
    list_schedule_for_day,
    list_wardrobe_items,
    monthly_budget_status,
    monthly_expense_summary,
    process_existing_receipt_text,
    update_budget_settings,
)
from app.schemas import (
    AssistantAnswer,
    AssistantAsk,
    AppleCalendarInfo,
    BudgetSettings,
    BudgetStatus,
    AppleCalendarStatus,
    CalendarImportResult,
    CalendarSource,
    CalendarSourceCreate,
    CalendarSyncResult,
    CalendarImportText,
    CalendarImportUrl,
    DailyBriefing,
    GroceryExpirySummary,
    LlmStatus,
    MonthlyExpenseSummary,
    OcrStatus,
    Receipt,
    ReceiptProcessText,
    ReceiptTextCreate,
    Grocery,
    GroceryCreate,
    ScheduleItem,
    ScheduleItemCreate,
    ShortcutLocationRequest,
    ShortcutLocationResponse,
    WardrobeItem,
    WardrobeBulkCreate,
    WardrobeItemCreate,
)
from app.services.assistant import answer_student_question
from app.services.apple_caldav import AppleCalDAVConfigError, discover_apple_calendars
from app.services.calendar_import import parse_ics_events
from app.services.calendar_sync import sync_calendar_sources
from app.services.llm import improve_answer_with_llm, llm_status
from app.services.planner import build_daily_briefing
from app.services.shortcuts import build_location_alert
from app.services.ocr import OcrUnavailableError, extract_text_from_image, tesseract_available
from app.services.receipts import parse_receipt_text
from app.services.weather import get_dresden_weather


app = FastAPI(title="Jarvis Student Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "agent": "Jarvis"}


@app.get("/daily-briefing", response_model=DailyBriefing)
async def daily_briefing(day: date | None = None) -> DailyBriefing:
    target_day = day or date.today()
    await sync_calendar_sources()
    weather = await get_dresden_weather()
    groceries = list_groceries()
    wardrobe = list_wardrobe_items()
    schedule = list_schedule_for_day(target_day)
    briefing = build_daily_briefing(weather, groceries, wardrobe, schedule, target_day)
    budget = monthly_budget_status(target_day.strftime("%Y-%m"))
    if budget["status"] != "on_track":
        briefing.alerts.append(budget["message"])
    return briefing


async def _build_assistant_context(day: date | None = None) -> tuple[DailyBriefing, list[dict], dict, dict]:
    target_day = day or date.today()
    await sync_calendar_sources()
    weather = await get_dresden_weather()
    groceries_data = list_groceries()
    wardrobe_data = list_wardrobe_items()
    schedule_data = list_schedule_for_day(target_day)
    briefing = build_daily_briefing(weather, groceries_data, wardrobe_data, schedule_data, target_day)
    month = target_day.strftime("%Y-%m")
    expenses_data = monthly_expense_summary(month)
    budget_data = monthly_budget_status(month)
    if budget_data["status"] != "on_track":
        briefing.alerts.append(budget_data["message"])
    return briefing, groceries_data, expenses_data, budget_data


@app.post("/assistant/ask", response_model=AssistantAnswer)
async def ask_assistant(payload: AssistantAsk) -> dict:
    target_day = _target_day_from_question(payload.question)
    briefing, groceries_data, expenses_data, budget_data = await _build_assistant_context(target_day)
    base_result = answer_student_question(
        payload.question,
        briefing,
        groceries_data,
        expenses_data,
        budget_data,
        target_day=target_day,
    )
    return await improve_answer_with_llm(
        payload.question,
        base_result,
        briefing,
        groceries_data,
        expenses_data,
        budget_data,
    )


@app.post("/shortcuts/location-alert", response_model=ShortcutLocationResponse)
def shortcuts_location_alert(payload: ShortcutLocationRequest) -> dict:
    return build_location_alert(payload.place, payload.trigger)


@app.post("/alexa/webhook")
async def alexa_webhook(payload: dict) -> dict:
    request = payload.get("request", {})
    request_type = request.get("type")

    if request_type == "LaunchRequest":
        text = (
            "Jarvis is ready. You can ask about your schedule, outfit, meals, shopping list, weather, or budget. "
            "For example, say: what should I wear today?"
        )
        return _alexa_response(text, should_end_session=False)
    elif request_type == "IntentRequest":
        intent = request.get("intent", {})
        intent_name = intent.get("name", "")
        if intent_name in {"AMAZON.CancelIntent", "AMAZON.StopIntent"}:
            return _alexa_response("Okay, closing Jarvis.", should_end_session=True)
        if intent_name == "AMAZON.FallbackIntent":
            return _alexa_response(
                "I did not catch that. Try asking: what should I wear today, or what should I eat after football?",
                should_end_session=False,
            )
        question = _question_from_alexa_intent(intent)
    else:
        question = "help"

    target_day = _target_day_from_question(question)
    briefing, groceries_data, expenses_data, budget_data = await _build_assistant_context(target_day)
    base_result = answer_student_question(
        question,
        briefing,
        groceries_data,
        expenses_data,
        budget_data,
        target_day=target_day,
    )
    result = await improve_answer_with_llm(
        question,
        base_result,
        briefing,
        groceries_data,
        expenses_data,
        budget_data,
    )
    should_end = result["intent"] != "help"
    return _alexa_response(result["answer"], should_end_session=should_end)


def _question_from_alexa_intent(intent: dict) -> str:
    name = intent.get("name", "")
    slots = intent.get("slots", {})
    free_question = slots.get("question", {}).get("value")
    if free_question:
        return free_question
    intent_questions = {
        "DailyBriefingIntent": "daily summary",
        "ScheduleIntent": "what is my schedule today",
        "OutfitIntent": "what should I wear today",
        "MealIntent": "what should I eat today",
        "ShoppingIntent": "what groceries should I buy",
        "BudgetIntent": "how much did I spend this month",
        "WeatherIntent": "what is the weather",
        "AMAZON.HelpIntent": "help",
    }
    return intent_questions.get(name, "daily summary")


def _target_day_from_question(question: str) -> date:
    normalized = question.lower()
    today = date.today()
    if "day after tomorrow" in normalized:
        return today + timedelta(days=2)
    if "tomorrow" in normalized:
        return today + timedelta(days=1)
    return today


def _alexa_response(text: str, should_end_session: bool = True) -> dict:
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": text,
            },
            "card": {
                "type": "Simple",
                "title": "Jarvis",
                "content": text,
            },
            "shouldEndSession": should_end_session,
        },
    }
    if not should_end_session:
        response["response"]["reprompt"] = {
            "outputSpeech": {
                "type": "PlainText",
                "text": "What would you like to ask Jarvis?",
            }
        }
    return response


@app.get("/groceries", response_model=list[Grocery])
def groceries() -> list[dict]:
    return list_groceries()


@app.get("/groceries/expiry", response_model=GroceryExpirySummary)
def groceries_expiry(day: date | None = None) -> dict:
    return grocery_expiry_summary(day or date.today())


@app.get("/llm/status", response_model=LlmStatus)
def llm_config_status() -> dict:
    return llm_status()


@app.post("/groceries", response_model=Grocery, status_code=201)
def add_grocery(payload: GroceryCreate) -> dict:
    return create_grocery(payload.model_dump())


@app.delete("/groceries/{grocery_id}", status_code=204)
def remove_grocery(grocery_id: int) -> None:
    try:
        delete_grocery(grocery_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Grocery not found") from exc


@app.get("/wardrobe", response_model=list[WardrobeItem])
def wardrobe() -> list[dict]:
    return list_wardrobe_items()


@app.post("/wardrobe", response_model=WardrobeItem, status_code=201)
def add_wardrobe_item(payload: WardrobeItemCreate) -> dict:
    return create_wardrobe_item(payload.model_dump())


@app.post("/wardrobe/bulk", response_model=list[WardrobeItem], status_code=201)
def add_wardrobe_bulk(payload: WardrobeBulkCreate) -> list[dict]:
    return [create_wardrobe_item(item.model_dump()) for item in payload.items]


@app.delete("/wardrobe/{item_id}", status_code=204)
def remove_wardrobe_item(item_id: int) -> None:
    try:
        delete_wardrobe_item(item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Wardrobe item not found") from exc


@app.post("/wardrobe/upload-photo", response_model=WardrobeItem, status_code=201)
async def upload_wardrobe_photo(
    name: str = Form(...),
    item_type: str = Form(...),
    color: str = Form(...),
    style: str = Form("casual"),
    warmth: int = Form(1),
    rain_ready: bool = Form(False),
    sport_ready: bool = Form(False),
    formality: str = Form("casual"),
    file: UploadFile = File(...),
) -> dict:
    WARDROBE_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "wardrobe.jpg").name
    relative_path = Path("wardrobe") / f"{uuid4().hex[:8]}-{safe_name}"
    target = UPLOADS_DIR / relative_path
    target.write_bytes(await file.read())
    return create_wardrobe_item(
        {
            "name": name,
            "item_type": item_type,
            "color": color,
            "style": style,
            "warmth": warmth,
            "rain_ready": rain_ready,
            "sport_ready": sport_ready,
            "formality": formality,
            "image_path": relative_path.as_posix(),
        }
    )


@app.get("/schedule", response_model=list[ScheduleItem])
def schedule(day: date | None = None) -> list[dict]:
    return list_schedule_for_day(day or date.today())


@app.post("/schedule", response_model=ScheduleItem, status_code=201)
def add_schedule_item(payload: ScheduleItemCreate) -> dict:
    return create_schedule_item(payload.model_dump())


@app.delete("/schedule/{schedule_id}", status_code=204)
def remove_schedule_item(schedule_id: int) -> None:
    try:
        delete_schedule_item(schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Schedule item not found") from exc


@app.post("/calendar/import-ics-url", response_model=CalendarImportResult)
async def import_apple_calendar_url(payload: CalendarImportUrl) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(payload.url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail="Could not fetch calendar URL") from exc

    events = parse_ics_events(response.text)
    return import_schedule_events(events)


@app.post("/calendar/import-ics-text", response_model=CalendarImportResult)
def import_apple_calendar_text(payload: CalendarImportText) -> dict:
    events = parse_ics_events(payload.raw_ics)
    return import_schedule_events(events)


@app.get("/calendar/sources", response_model=list[CalendarSource])
def calendar_sources() -> list[dict]:
    return list_calendar_sources()


@app.post("/calendar/sources", response_model=CalendarSource, status_code=201)
def add_calendar_source(payload: CalendarSourceCreate) -> dict:
    return create_calendar_source(payload.model_dump())


@app.delete("/calendar/sources/{source_id}", status_code=204)
def remove_calendar_source(source_id: int) -> None:
    try:
        delete_calendar_source(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Calendar source not found") from exc


@app.post("/calendar/sync", response_model=CalendarSyncResult)
async def sync_calendar() -> dict:
    return await sync_calendar_sources()


@app.get("/calendar/apple/status", response_model=AppleCalendarStatus)
def apple_calendar_status() -> dict[str, str | bool]:
    configured = bool(APPLE_CALDAV_USERNAME and APPLE_CALDAV_PASSWORD)
    message = (
        "Apple CalDAV credentials are configured."
        if configured
        else "Set APPLE_CALDAV_USERNAME and APPLE_CALDAV_PASSWORD in backend/.env."
    )
    return {"configured": configured, "message": message}


@app.get("/calendar/apple/calendars", response_model=list[AppleCalendarInfo])
async def apple_calendar_list() -> list[dict]:
    try:
        return await discover_apple_calendars()
    except AppleCalDAVConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=400,
            detail="Apple Calendar rejected the request. Check your Apple ID and app-specific password.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail="Could not connect to Apple Calendar.") from exc


@app.get("/receipts", response_model=list[Receipt])
def receipts() -> list[dict]:
    return list_receipts()


@app.delete("/receipts/{receipt_id}", status_code=204)
def remove_receipt(receipt_id: int) -> None:
    try:
        delete_receipt(receipt_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc


@app.post("/receipts/from-text", response_model=Receipt, status_code=201)
def add_receipt_from_text(payload: ReceiptTextCreate) -> dict:
    purchased_on = date.fromisoformat(payload.purchased_on)
    items = parse_receipt_text(payload.raw_text)
    return create_receipt_from_items(
        store=payload.store,
        purchased_on=purchased_on,
        raw_text=payload.raw_text,
        items=items,
    )


@app.post("/receipts/upload-photo", response_model=Receipt, status_code=201)
async def upload_receipt_photo(
    store: str = Form(...),
    purchased_on: date = Form(...),
    file: UploadFile = File(...),
) -> dict:
    RECEIPT_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "receipt.jpg").name
    relative_path = Path("receipts") / f"{purchased_on.isoformat()}-{uuid4().hex[:8]}-{safe_name}"
    target = UPLOADS_DIR / relative_path
    target.write_bytes(await file.read())
    return create_receipt_from_items(
        store=store,
        purchased_on=purchased_on,
        raw_text=None,
        items=[],
        image_path=relative_path.as_posix(),
        status="uploaded_needs_ocr",
    )


@app.post("/receipts/scan-photo", response_model=Receipt, status_code=201)
async def scan_receipt_photo(
    store: str = Form(...),
    purchased_on: date = Form(...),
    file: UploadFile = File(...),
) -> dict:
    RECEIPT_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "receipt.jpg").name
    relative_path = Path("receipts") / f"{purchased_on.isoformat()}-{uuid4().hex[:8]}-{safe_name}"
    target = UPLOADS_DIR / relative_path
    target.write_bytes(await file.read())

    try:
        raw_text = extract_text_from_image(str(target))
    except OcrUnavailableError as exc:
        return create_receipt_from_items(
            store=store,
            purchased_on=purchased_on,
            raw_text=str(exc),
            items=[],
            image_path=relative_path.as_posix(),
            status="uploaded_needs_ocr",
        )

    items = parse_receipt_text(raw_text)
    return create_receipt_from_items(
        store=store,
        purchased_on=purchased_on,
        raw_text=raw_text,
        items=items,
        image_path=relative_path.as_posix(),
    )


@app.post("/receipts/{receipt_id}/process-text", response_model=Receipt)
def process_receipt_text(receipt_id: int, payload: ReceiptProcessText) -> dict:
    items = parse_receipt_text(payload.raw_text)
    try:
        return process_existing_receipt_text(receipt_id, payload.raw_text, items)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Receipt not found") from exc


@app.get("/ocr/status", response_model=OcrStatus)
def ocr_status() -> dict[str, str | bool]:
    available = tesseract_available()
    message = (
        "Tesseract OCR is available."
        if available
        else "Tesseract OCR is not available on PATH. Receipt photos can be uploaded, but automatic OCR will wait."
    )
    return {"available": available, "message": message}


@app.get("/expenses/monthly", response_model=MonthlyExpenseSummary)
def expenses_monthly(month: str | None = None) -> dict:
    target_month = month or date.today().strftime("%Y-%m")
    return monthly_expense_summary(target_month)


@app.get("/budget", response_model=BudgetSettings)
def budget_settings() -> dict:
    return get_budget_settings()


@app.put("/budget", response_model=BudgetSettings)
def update_budget(payload: BudgetSettings) -> dict:
    return update_budget_settings(payload.model_dump())


@app.get("/budget/status", response_model=BudgetStatus)
def budget_status(month: str | None = None) -> dict:
    target_month = month or date.today().strftime("%Y-%m")
    return monthly_budget_status(target_month)
