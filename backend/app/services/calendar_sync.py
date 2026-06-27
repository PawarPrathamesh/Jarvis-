from pathlib import Path

import httpx

from app.repositories import (
    import_schedule_events,
    list_active_calendar_sources,
    mark_calendar_source_synced,
)
from app.services.calendar_import import parse_ics_events


async def sync_calendar_sources() -> dict:
    totals = {"sources": 0, "imported": 0, "updated": 0, "skipped": 0, "errors": []}
    for source in list_active_calendar_sources():
        totals["sources"] += 1
        try:
            raw_ics = await _read_source(source)
            result = import_schedule_events(parse_ics_events(raw_ics))
            mark_calendar_source_synced(source["id"])
            totals["imported"] += result["imported"]
            totals["updated"] += result.get("updated", 0)
            totals["skipped"] += result["skipped"]
        except Exception as exc:
            totals["errors"].append(f"{source['name']}: {exc}")
    return totals


async def _read_source(source: dict) -> str:
    source_type = source["source_type"]
    value = source["value"]
    if source_type == "file":
        path = Path(value)
        if not path.is_absolute():
            path = Path.cwd().parent / value
        return path.read_text(encoding="utf-8")
    if source_type == "url":
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(value)
            response.raise_for_status()
            return response.text
    raise ValueError(f"Unsupported calendar source type: {source_type}")
