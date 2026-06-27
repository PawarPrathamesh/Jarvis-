from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_ics_events(raw_ics: str) -> list[dict]:
    events: list[dict] = []
    for block in _event_blocks(_unfold_ics(raw_ics)):
        event = _parse_event(block)
        if event:
            events.append(event)
    return events


def _unfold_ics(raw_ics: str) -> list[str]:
    lines: list[str] = []
    for line in raw_ics.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not line:
            continue
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _event_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line == "BEGIN:VEVENT":
            current = []
        elif line == "END:VEVENT" and current is not None:
            blocks.append(current)
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def _parse_event(lines: list[str]) -> dict | None:
    values: dict[str, str] = {}
    params: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key_part, value = line.split(":", 1)
        key_bits = key_part.split(";")
        key = key_bits[0].upper()
        values[key] = _clean_ics_text(value)
        params[key] = key_part

    starts_at = _parse_datetime(values.get("DTSTART"), params.get("DTSTART", ""))
    if starts_at is None:
        return None

    ends_at = _parse_datetime(values.get("DTEND"), params.get("DTEND", "")) or starts_at
    title = values.get("SUMMARY") or "Apple Calendar event"
    location = values.get("LOCATION") or None
    external_id = values.get("UID") or f"{title}-{starts_at}"

    return {
        "title": title,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "location": location,
        "activity_type": _guess_activity_type(title),
        "near_store": None,
        "external_id": external_id,
        "source": "apple_calendar",
    }


def _parse_datetime(value: str | None, key_part: str) -> str | None:
    if not value:
        return None
    try:
        if "VALUE=DATE" in key_part:
            return datetime.strptime(value, "%Y%m%d").date().isoformat()
        if value.endswith("Z"):
            parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
            return parsed.astimezone().replace(tzinfo=None).isoformat(timespec="minutes")
        return datetime.strptime(value, "%Y%m%dT%H%M%S").isoformat(timespec="minutes")
    except ValueError:
        try:
            return parsedate_to_datetime(value).replace(tzinfo=None).isoformat(timespec="minutes")
        except (TypeError, ValueError):
            return None


def _clean_ics_text(value: str) -> str:
    return (
        value.replace("\\n", " ")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def _guess_activity_type(title: str) -> str:
    lowered = title.lower()
    if "football" in lowered:
        return "football"
    if "gym" in lowered:
        return "gym"
    if "study" in lowered:
        return "study"
    if any(word in lowered for word in ["lecture", "class", "seminar", "lab"]):
        return "lecture"
    return "event"
