# Jarvis Student Agent

Jarvis is a local-first personal assistant for student life. It is being built for a TU Dresden master's student to reduce daily decision fatigue around schedule, clothing, meals, groceries, receipts, and budget.

The goal is to turn scattered context into one useful daily briefing:

```text
Today you have a lecture at TU Dresden, football in the evening, light rain after noon, and chicken expiring soon.
Wear a rain-ready jacket, hoodie, dark jeans, and comfortable shoes.
Breakfast: oats with banana and yogurt.
Lunch: rice bowl with tomatoes and eggs.
Dinner after football: high-protein chicken rice bowl.
You are near Aldi after campus, so buy milk and bananas.
```

## Vision

Jarvis should become a private, PC-hosted student-life copilot that can:

- read schedule data from Apple Calendar
- fetch Dresden weather
- suggest outfits from a real photo-backed wardrobe
- track groceries from manual entries and receipt scans
- plan meals around groceries, expiry dates, budget, and activity
- track monthly food spending
- remind the user about shopping opportunities near campus
- later speak through a Bluetooth speaker like a home assistant

## Current Features

### Daily Briefing

- Weather for Dresden through Open-Meteo.
- Schedule-aware daily summary.
- Outfit suggestions using weather, activity, and wardrobe metadata.
- Meal suggestions based on available groceries and sports activity.
- Alerts for rain, football, expiring groceries, and budget pressure.

### Dashboard

The React dashboard runs locally and provides:

- daily briefing
- groceries
- wardrobe with photos
- schedule management
- Apple Calendar source sync
- receipt text/photo workflow
- monthly expense and budget status
- OCR status

Frontend URL:

```text
http://127.0.0.1:5173
```

Backend API docs:

```text
http://127.0.0.1:8000/docs
```

Full operating guide:

```text
docs/HOW_TO_USE_JARVIS.md
```

### Groceries And Meal Planning

- Add groceries manually.
- Track category, quantity, store, price, and expiry date.
- Receipt items can automatically create grocery inventory entries.
- Meal planning prioritizes available ingredients and expiring food.

### Receipt Scanning And Expenses

Jarvis supports:

- receipt text parsing
- receipt photo upload
- Tesseract OCR integration
- manual correction when OCR is unavailable or inaccurate
- automatic grocery updates from food items
- monthly spending summaries by category
- budget status and saving suggestions

If Tesseract is not installed or not on PATH, Jarvis still stores receipt photos as `uploaded_needs_ocr` and lets you paste corrected text later.

### Wardrobe Photos

Wardrobe items can include photos and metadata:

- item type
- color
- style
- warmth
- rain readiness
- sport readiness
- formality

Images are stored locally under:

```text
backend/uploads/wardrobe
```

To feed your real clothes into Jarvis, use the dashboard `Wardrobe` panel.

For best outfit recommendations, add at least:

- 1-2 jackets
- 4-6 tops
- 3-4 bottoms
- 2-3 shoes
- sport/football clothes if you want post-lecture sport planning

Each item should have:

```text
name, item type, color, style, warmth, rain ready, sport ready, formality, photo if possible
```

Warmth is from `1` light to `5` very warm. Good style tags are things like `casual`, `minimal`, `sport`, `smart`, `streetwear`, `formal`, or combinations like `casual minimal`.

For fast setup, use the bulk format in the dashboard:

```text
black rain jacket,jacket,black,casual minimal,4,true,false,casual
grey hoodie,top,grey,casual,3,false,false,casual
white sneakers,shoes,white,casual,1,false,false,casual
```

An example template is available at:

```text
data_templates/wardrobe-bulk-example.csv
```

### Apple Calendar Sync

Jarvis syncs Apple Calendar through iCloud CalDAV. This is the backend route for private calendar data without manually exporting `.ics` files.

Credentials are stored only in local `backend/.env`, which is ignored by Git.

## Tech Stack

```text
Backend:   Python, FastAPI
Frontend:  React, Vite
Database:  SQLite
Weather:   Open-Meteo
Calendar:  Apple iCloud CalDAV
OCR:       Tesseract OCR
Storage:   Local filesystem uploads
```

## Project Structure

```text
jarvis/
  backend/
    app/
      main.py
      database.py
      repositories.py
      schemas.py
      services/
        apple_caldav.py
        calendar_import.py
        calendar_sync.py
        ocr.py
        planner.py
        receipts.py
        weather.py
    data/
    uploads/
    requirements.txt
    .env.example

  frontend/
    src/
      api.js
      main.jsx
      styles.css
    package.json
```

## Local Setup

### Backend

```powershell
cd F:\Projects\jarvis\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `python` is not available on PATH, use the interpreter inside `.venv` once it exists:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```powershell
cd F:\Projects\jarvis\frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Apple Calendar Setup

1. Create an Apple app-specific password from your Apple Account security settings.
2. Copy the local config template:

```powershell
cd F:\Projects\jarvis\backend
copy .env.example .env
```

3. Edit `backend/.env`:

```text
APPLE_CALDAV_USERNAME=your-apple-id@example.com
APPLE_CALDAV_PASSWORD=your-app-specific-password
APPLE_CALDAV_CALENDAR_NAME=
APPLE_CALDAV_BASE_URL=https://caldav.icloud.com
```

4. Restart the backend.
5. Check:

```text
http://127.0.0.1:8000/calendar/apple/status
```

6. List available iCloud calendars:

```text
http://127.0.0.1:8000/calendar/apple/calendars
```

If you want a specific calendar, copy its exact `name` into:

```text
APPLE_CALDAV_CALENDAR_NAME=Calendar
```

Then restart the backend again.

7. In the dashboard Schedule panel:

- click `Link Apple`
- click `Sync saved calendars`

Jarvis also syncs saved calendar sources when the daily briefing loads.

## Tesseract OCR Setup

After installing Tesseract on Windows, restart the terminal or PC so PATH updates.

Check:

```powershell
tesseract --version
```

Then check Jarvis:

```text
http://127.0.0.1:8000/ocr/status
```

If configured correctly, Jarvis will attempt automatic OCR when receipt photos are uploaded.

## Main API Endpoints

```text
GET  /health
GET  /daily-briefing
POST /assistant/ask
POST /alexa/webhook

GET  /groceries
POST /groceries
DELETE /groceries/{grocery_id}

GET  /wardrobe
POST /wardrobe
POST /wardrobe/upload-photo
DELETE /wardrobe/{item_id}

GET  /schedule
POST /schedule
DELETE /schedule/{schedule_id}

GET  /calendar/apple/status
GET  /calendar/sources
POST /calendar/sources
POST /calendar/sync
DELETE /calendar/sources/{source_id}

GET  /receipts
POST /receipts/from-text
POST /receipts/upload-photo
POST /receipts/scan-photo
POST /receipts/{receipt_id}/process-text
DELETE /receipts/{receipt_id}

GET  /expenses/monthly

GET  /budget
PUT  /budget
GET  /budget/status

GET  /ocr/status
```

## Privacy Notes

Jarvis is designed as a local-first personal project.

- SQLite data stays on your PC.
- Uploaded wardrobe and receipt photos stay under `backend/uploads`.
- `.env` is ignored by Git and should contain credentials only locally.
- `.ics` files are ignored by Git because they may expose private calendar data.
- Apple Calendar uses an app-specific password, not your normal Apple ID password.

## What You Need To Provide

Do not paste passwords into chat. Put secrets only in `backend/.env`.

### Apple Calendar

- Apple ID email.
- Apple app-specific password.
- Optional calendar name if you want Jarvis to sync only one calendar.

Create the app-specific password from your Apple Account security settings, then set:

```text
APPLE_CALDAV_USERNAME=your-apple-id@example.com
APPLE_CALDAV_PASSWORD=your-app-specific-password
APPLE_CALDAV_CALENDAR_NAME=
```

### Alexa

For Alexa integration we need:

- Amazon Developer account.
- Alexa Custom Skill named `Jarvis`.
- A public HTTPS URL for Jarvis, either a temporary tunnel for testing or cloud deployment.
- Later, the Alexa Skill ID saved in `ALEXA_SKILL_ID`.

The backend now includes:

```text
POST /assistant/ask
POST /alexa/webhook
```

`/assistant/ask` powers the dashboard question box. `/alexa/webhook` returns Alexa-compatible speech responses and will become the skill endpoint.

The working Alexa interaction model is stored in:

```text
alexa/interaction-model-en-US.json
```

Paste that file into `Build > Interaction Model > JSON Editor`, then click `Save Model` and `Build Model`.

For local testing with ngrok:

```powershell
cd F:\Projects\jarvis\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
ngrok http 8000
```

Use the HTTPS ngrok URL with `/alexa/webhook` as the Alexa endpoint.

Schedule questions understand simple relative dates:

```text
ask jarvis tell me what is my schedule today
ask jarvis tell me what is my schedule tomorrow
ask jarvis tell me what is my schedule day after tomorrow
```

### iPhone Location Later

For iPhone location alerts, the easiest personal-project route is Apple Shortcuts:

- create a Shortcut automation for arriving near Aldi/Rewe/Lidl or leaving TU Dresden
- send a webhook request to Jarvis
- let Jarvis answer with a shopping reminder

This avoids needing a full iOS app in the first version.

## Roadmap

### Short Term

- Improve Apple Calendar sync reliability and event filtering.
- Add edit/delete controls for groceries, wardrobe, schedule, and receipts.
- Add better receipt OCR cleanup for German supermarket receipts.
- Add dashboard views for weekly spending and grocery expiry.

### Wardrobe Intelligence

- Improve outfit scoring using color harmony, style tags, weather, and activity.
- Add laundry/availability state.
- Add outfit history so Jarvis avoids repeating the same outfit too often.
- Later: use vision models or image embeddings for better clothing understanding.

### Meal Intelligence

- Add recipe database.
- Generate meals from groceries and expiry dates.
- Add football/gym recovery meals.
- Add cheap student meal mode.
- Add Mensa comparison later.

### Voice Jarvis

- Add dashboard question endpoint.
- Add Alexa Custom Skill webhook.
- Add wake word for PC-only mode later.
- Add speech-to-text and text-to-speech for Bluetooth speaker.
- Output daily briefing through Bluetooth speaker or Alexa.

### iPhone Integration

- Apple Shortcuts webhook for location-aware reminders.
- Shopping alerts near Aldi/Rewe/Lidl.
- Faster photo upload from phone to Jarvis.

## Current Development Status

Jarvis is a working local MVP with backend, dashboard, receipt workflow, Apple Calendar CalDAV foundation, wardrobe photos, budget tracking, and weather-based daily briefing.

The next major development step is to improve the intelligence layer: better outfit matching and smarter meal planning from real groceries.
