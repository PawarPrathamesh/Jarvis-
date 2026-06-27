# Jarvis Student Agent

Jarvis is a personal student-life assistant for daily planning. The first MVP is a local FastAPI backend that combines Dresden weather, schedule, groceries, wardrobe items, and simple planning rules to produce a daily briefing.

## MVP Features

- Weather briefing for Dresden through Open-Meteo.
- SQLite-backed groceries, wardrobe items, schedule items, and preferences.
- Rule-based daily outfit, meal, shopping, and alert recommendations.
- API endpoints to list and add groceries, wardrobe items, and schedule events.
- Seed data so the first briefing works immediately.

## Run Locally

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

## First API Endpoints

```text
GET  /health
GET  /daily-briefing
GET  /groceries
POST /groceries
GET  /wardrobe
POST /wardrobe
GET  /schedule
POST /schedule
GET  /receipts
POST /receipts/from-text
POST /receipts/upload-photo
GET  /expenses/monthly
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

## Next Milestones

1. Add CRUD endpoints for groceries, wardrobe, and schedule.
2. Add receipt photo upload and OCR parsing.
3. Add expense tracking and monthly savings insights.
4. Add wardrobe photo upload and aesthetic outfit scoring.
5. Add voice input/output and iPhone Shortcut hooks.
