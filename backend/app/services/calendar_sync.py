import httpx

from app.repositories import (
    import_schedule_events,
    list_active_calendar_sources,
    mark_calendar_source_synced,
)
from app.services.apple_caldav import fetch_apple_calendar_events
from app.services.calendar_import import parse_ics_events


async def sync_calendar_sources() -> dict:
    totals = {"sources": 0, "imported": 0, "updated": 0, "skipped": 0, "errors": []}
    for source in list_active_calendar_sources():
        totals["sources"] += 1
        try:
            events = await _read_source_events(source)
            result = import_schedule_events(events)
            mark_calendar_source_synced(source["id"])
            totals["imported"] += result["imported"]
            totals["updated"] += result.get("updated", 0)
            totals["skipped"] += result["skipped"]
        except Exception as exc:
            totals["errors"].append(f"{source['name']}: {exc}")
    return totals


async def _read_source_events(source: dict) -> list[dict]:
    source_type = source["source_type"]
    value = source["value"]
    if source_type == "url":
        url = _calendar_url(value)
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            response.raise_for_status()
            return parse_ics_events(response.text)
    if source_type == "apple_caldav":
        calendar_url = value if value.startswith("http") else None
        return await fetch_apple_calendar_events(calendar_url)
    raise ValueError(f"Unsupported calendar source type: {source_type}")


def _calendar_url(value: str) -> str:
    if value.startswith("webcal://"):
        return f"https://{value.removeprefix('webcal://')}"
    return value
