from datetime import date
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import UPLOADS_DIR
from app.database import initialize_database
from app.repositories import (
    create_grocery,
    create_receipt_from_items,
    create_schedule_item,
    create_wardrobe_item,
    list_receipts,
    list_groceries,
    list_schedule_for_day,
    list_wardrobe_items,
    monthly_expense_summary,
    process_existing_receipt_text,
)
from app.schemas import (
    DailyBriefing,
    MonthlyExpenseSummary,
    OcrStatus,
    Receipt,
    ReceiptProcessText,
    ReceiptTextCreate,
    Grocery,
    GroceryCreate,
    ScheduleItem,
    ScheduleItemCreate,
    WardrobeItem,
    WardrobeItemCreate,
)
from app.services.planner import build_daily_briefing
from app.services.ocr import OcrUnavailableError, extract_text_from_image, tesseract_available
from app.services.receipts import parse_receipt_text
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


@app.get("/receipts", response_model=list[Receipt])
def receipts() -> list[dict]:
    return list_receipts()


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
    store: str,
    purchased_on: date,
    file: UploadFile = File(...),
) -> dict:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "receipt.jpg").name
    target = UPLOADS_DIR / f"{purchased_on.isoformat()}-{uuid4().hex[:8]}-{safe_name}"
    target.write_bytes(await file.read())
    return create_receipt_from_items(
        store=store,
        purchased_on=purchased_on,
        raw_text=None,
        items=[],
        image_path=str(target),
        status="uploaded_needs_ocr",
    )


@app.post("/receipts/scan-photo", response_model=Receipt, status_code=201)
async def scan_receipt_photo(
    store: str,
    purchased_on: date,
    file: UploadFile = File(...),
) -> dict:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "receipt.jpg").name
    target = UPLOADS_DIR / f"{purchased_on.isoformat()}-{uuid4().hex[:8]}-{safe_name}"
    target.write_bytes(await file.read())

    try:
        raw_text = extract_text_from_image(str(target))
    except OcrUnavailableError as exc:
        return create_receipt_from_items(
            store=store,
            purchased_on=purchased_on,
            raw_text=str(exc),
            items=[],
            image_path=str(target),
            status="uploaded_needs_ocr",
        )

    items = parse_receipt_text(raw_text)
    return create_receipt_from_items(
        store=store,
        purchased_on=purchased_on,
        raw_text=raw_text,
        items=items,
        image_path=str(target),
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
