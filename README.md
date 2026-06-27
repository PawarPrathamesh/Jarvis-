# Jarvis Student Agent

Jarvis is a personal student-life assistant for daily planning. The first MVP is a local FastAPI backend that combines Dresden weather, schedule, groceries, wardrobe items, and simple planning rules to produce a daily briefing.

## MVP Features

- Weather briefing for Dresden through Open-Meteo.
- SQLite-backed groceries, wardrobe items, schedule items, and preferences.
- Rule-based daily outfit, meal, shopping, and alert recommendations.
- API endpoints to list and add groceries, wardrobe items, and schedule events.
- Seed data so the first briefing works immediately.

## Run Locally

Backend:

```powershell
cd F:\Projects\jarvis\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/daily-briefing
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Frontend:

```powershell
cd F:\Projects\jarvis\frontend
npm install
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```

## First API Endpoints

```text
GET  /health
GET  /daily-briefing
GET  /groceries
POST /groceries
GET  /wardrobe
POST /wardrobe
POST /wardrobe/upload-photo
GET  /schedule
POST /schedule
POST /calendar/import-ics-url
POST /calendar/import-ics-text
GET  /receipts
POST /receipts/from-text
POST /receipts/upload-photo
POST /receipts/scan-photo
POST /receipts/{receipt_id}/process-text
GET  /expenses/monthly
GET  /ocr/status
GET  /budget
PUT  /budget
GET  /budget/status
```

Example receipt text payload:

```json
{
  "store": "Aldi",
  "purchased_on": "2026-06-27",
  "raw_text": "Milk 1,09\nEggs 2,49\nChicken 4,99\nChocolate 1,59\nTOTAL 10,16"
}
```

Jarvis will parse the line items, add food items to the grocery inventory, keep snack/household items out of groceries, and include everything in monthly spending summaries.

Receipt photo workflow:

- `POST /receipts/upload-photo` stores a receipt image and marks it as `uploaded_needs_ocr`.
- `POST /receipts/scan-photo` stores a receipt image and attempts OCR with Tesseract.
- `GET /ocr/status` tells you whether Tesseract is available on this machine.
- `POST /receipts/{receipt_id}/process-text` lets you paste corrected OCR text for an uploaded receipt.

If Tesseract is not installed or not on PATH, Jarvis still stores the receipt photo safely and waits for manual text or future OCR setup.

Budget endpoints:

- `GET /budget` shows current monthly budget settings.
- `PUT /budget` updates food, snack, and eating-out budgets.
- `GET /budget/status?month=2026-06` compares tracked spending against the monthly food budget.

## Apple Calendar Import

Jarvis can import Apple Calendar events from an `.ics` calendar URL or from a local `.ics` file.

On iPhone or Mac:

1. Open Apple Calendar.
2. Choose the calendar you want Jarvis to read.
3. Enable calendar sharing/publishing for that calendar.
4. Copy the public/subscription `.ics` URL.
5. Paste it into the Jarvis dashboard Schedule panel and press Import.

The imported events are saved into the `schedule_items` table with `source = apple_calendar`, so the daily briefing can use them like manually added lectures or football sessions.

For dynamic sync:

1. Put the `.ics` file in `F:\Projects\jarvis`, or use the online `.ics` URL.
2. In the dashboard Schedule panel, save it as a calendar source.
3. Press `Sync saved calendars`.
4. Jarvis will also sync saved calendar sources automatically when the daily briefing loads.

Local `.ics` files are ignored by Git because they may contain private schedule data.

## Wardrobe Photos

The dashboard Wardrobe panel accepts an image file when adding a clothing item. Jarvis stores the image under:

```text
backend/uploads/wardrobe
```

The API serves stored images through:

```text
http://127.0.0.1:8000/uploads/...
```

This gives Jarvis a photo-backed wardrobe database for more accurate outfit planning later.

## Next Milestones

1. Add CRUD endpoints for groceries, wardrobe, and schedule.
2. Add receipt photo upload and OCR parsing.
3. Add expense tracking and monthly savings insights.
4. Add wardrobe photo upload and aesthetic outfit scoring.
5. Add voice input/output and iPhone Shortcut hooks.
