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
GET  /calendar/apple/status
GET  /calendar/sources
POST /calendar/sources
POST /calendar/sync
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

The dashboard Receipt panel supports this same flow:

1. Upload a receipt photo.
2. Jarvis attempts OCR if Tesseract is installed.
3. If OCR is unavailable, the receipt is saved as `uploaded_needs_ocr`.
4. Select that receipt, paste corrected text, and apply it.
5. Jarvis updates groceries and monthly expenses.

Budget endpoints:

- `GET /budget` shows current monthly budget settings.
- `PUT /budget` updates food, snack, and eating-out budgets.
- `GET /budget/status?month=2026-06` compares tracked spending against the monthly food budget.

## Apple Calendar Sync

Jarvis syncs Apple Calendar through iCloud CalDAV. This is the backend route for private Apple Calendar data without relying on manually exported `.ics` files.

Create a local backend config:

```powershell
cd F:\Projects\jarvis\backend
copy .env.example .env
```

Edit `backend/.env`:

```text
APPLE_CALDAV_USERNAME=your-apple-id@example.com
APPLE_CALDAV_PASSWORD=your-app-specific-password
APPLE_CALDAV_CALENDAR_NAME=
APPLE_CALDAV_BASE_URL=https://caldav.icloud.com
```

Use an Apple app-specific password, not your normal Apple ID password. Create one from your Apple Account security settings.

Then restart the FastAPI backend and open:

```text
GET http://127.0.0.1:8000/calendar/apple/status
```

The dashboard Schedule panel can save an Apple Calendar source and run `Sync saved calendars`. Jarvis also syncs saved calendar sources when the daily briefing loads.

Local `.ics` files are ignored by Git because they may contain private schedule data, but the dashboard no longer uses local files for calendar sync.

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
