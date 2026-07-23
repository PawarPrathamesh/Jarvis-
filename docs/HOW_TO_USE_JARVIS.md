# How To Use Jarvis

This guide explains how to start, restart, stop, access, and test Jarvis on your Windows PC.

## Main URLs

```text
Dashboard:       http://127.0.0.1:5173
Backend health:  http://127.0.0.1:8000/health
Backend docs:    http://127.0.0.1:8000/docs
Alexa webhook:   http://127.0.0.1:8000/alexa/webhook
LLM status:      http://127.0.0.1:8000/llm/status
```

## Start Jarvis

Open one PowerShell terminal for the backend:

```powershell
cd F:\Projects\jarvis\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open a second PowerShell terminal for the dashboard:

```powershell
cd F:\Projects\jarvis\frontend
npm run dev
```

Then open:

```text
http://127.0.0.1:5173
```

## Restart Jarvis Backend

In the backend terminal, press:

```text
Ctrl + C
```

Then start it again:

```powershell
cd F:\Projects\jarvis\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","agent":"Jarvis"}
```

## Stop Jarvis

Stop backend:

```text
Ctrl + C
```

Stop frontend:

```text
Ctrl + C
```

If a hidden backend process is running, find it:

```powershell
Get-Process | Where-Object { $_.ProcessName -like '*python*' } | Select-Object ProcessName,Id,StartTime,Path
```

Stop the backend process by ID:

```powershell
Stop-Process -Id YOUR_PROCESS_ID
```

## Start Alexa Testing

Jarvis backend must already be running on port `8000`.

Start ngrok:

```powershell
ngrok http 8000
```

Copy the HTTPS URL from ngrok, for example:

```text
https://example.ngrok-free.dev
```

In Alexa Developer Console, set endpoint:

```text
https://example.ngrok-free.dev/alexa/webhook
```

Then test:

```text
open jarvis
ask jarvis tell me what is my schedule today
ask jarvis tell me what is my schedule tomorrow
ask jarvis tell me what should I wear today
ask jarvis tell me what should I eat after football
ask jarvis tell me what groceries should I buy
ask jarvis tell me how much did I spend this month
```

## Update Alexa Interaction Model

Use this file:

```text
F:\Projects\jarvis\alexa\interaction-model-en-US.json
```

In Alexa Developer Console:

```text
Build > Interaction Model > JSON Editor
```

Paste the JSON, then:

```text
Save Model
Build Model
```

## Apple Calendar Setup

Create or edit:

```text
F:\Projects\jarvis\backend\.env
```

Add:

```text
APPLE_CALDAV_USERNAME=your-apple-id@example.com
APPLE_CALDAV_PASSWORD=your-app-specific-password
APPLE_CALDAV_CALENDAR_NAME=
APPLE_CALDAV_BASE_URL=https://caldav.icloud.com
```

Restart backend after editing `.env`.

Check status:

```text
http://127.0.0.1:8000/calendar/apple/status
```

List calendars:

```text
http://127.0.0.1:8000/calendar/apple/calendars
```

Sync calendars from dashboard:

```text
Schedule panel > Link Apple > Sync saved calendars
```

Or sync from PowerShell:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/calendar/sync -Method Post
```

## Feed Wardrobe Data

Use the dashboard:

```text
http://127.0.0.1:5173
```

Go to the `Wardrobe` panel.

For best outfit answers, add photos and metadata for:

```text
jacket
top
bottom
shoes
sport
```

Bulk format:

```text
name,item_type,color,style,warmth,rain_ready,sport_ready,formality
```

Example:

```text
black rain jacket,jacket,black,casual minimal,4,true,false,casual
grey hoodie,top,grey,casual,3,false,false,casual
white sneakers,shoes,white,casual,1,false,false,casual
black joggers,bottom,black,sport casual,2,false,true,casual
```

Template:

```text
F:\Projects\jarvis\data_templates\wardrobe-bulk-example.csv
```

## Feed Grocery And Receipt Data

Use the dashboard `Groceries` panel for manual groceries.

Use the `Receipt Text` panel for:

```text
receipt photo scan
manual receipt text
OCR correction
```

Check OCR:

```text
http://127.0.0.1:8000/ocr/status
```

## Enable Optional AI Reasoning

Jarvis works without an LLM. To enable natural AI answers, edit:

```text
F:\Projects\jarvis\backend\.env
```

Add:

```text
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

Restart backend, then check:

```text
http://127.0.0.1:8000/llm/status
```

If enabled, `/assistant/ask` and Alexa answers can use the LLM while staying grounded in Jarvis data.

## Useful API Commands

Health:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/health
```

Daily briefing:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/daily-briefing
```

Ask Jarvis:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/assistant/ask -Method Post -ContentType 'application/json' -Body '{"question":"what should I wear today"}'
```

Schedule tomorrow:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/assistant/ask -Method Post -ContentType 'application/json' -Body '{"question":"what is my schedule tomorrow"}'
```

Calendar sync:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/calendar/sync -Method Post
```

Grocery expiry:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/groceries/expiry
```

LLM status:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/llm/status
```

Budget:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/budget/status
```

## Common Problems

### Apple Calendar says not configured

Make sure this file exists:

```text
F:\Projects\jarvis\backend\.env
```

Then restart backend.

### Alexa says it cannot help

Check:

```text
Backend is running
ngrok is running
Alexa endpoint uses /alexa/webhook
Alexa test mode is Development
Interaction model was rebuilt
```

### Alexa works for today but not tomorrow

Update Alexa model from:

```text
F:\Projects\jarvis\alexa\interaction-model-en-US.json
```

Then `Save Model` and `Build Model`.

### Port 8000 is already used

Find backend processes:

```powershell
Get-Process | Where-Object { $_.ProcessName -like '*python*' } | Select-Object ProcessName,Id,StartTime,Path
```

Stop the stale backend process:

```powershell
Stop-Process -Id YOUR_PROCESS_ID
```

## Git Commands

Check status:

```powershell
cd F:\Projects\jarvis
git status
```

Pull latest:

```powershell
git pull
```

Push changes:

```powershell
git push
```

## Run Tests

Backend tests:

```powershell
cd F:\Projects\jarvis\backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend production build:

```powershell
cd F:\Projects\jarvis\frontend
npm run build
```

GitHub Actions runs both checks automatically on push and pull request.
