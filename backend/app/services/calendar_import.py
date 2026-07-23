from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime


WEEKDAY_INDEX = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}


def parse_ics_events(raw_ics: str) -> list[dict]:
    events: list[dict] = []
    for block in _event_blocks(_unfold_ics(raw_ics)):
        events.extend(_parse_event(block))
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


def _parse_event(lines: list[str]) -> list[dict]:
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
        return []

    ends_at = _parse_datetime(values.get("DTEND"), params.get("DTEND", "")) or starts_at
    title = values.get("SUMMARY") or "Apple Calendar event"
    location = values.get("LOCATION") or None
    external_id = values.get("UID") or f"{title}-{starts_at}"
    base_event = {
        "title": title,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "location": location,
        "activity_type": _guess_activity_type(title),
        "near_store": None,
        "external_id": external_id,
        "source": "apple_calendar",
    }
    if values.get("RRULE"):
        return _expand_recurring_event(base_event, values["RRULE"])
    return [base_event]


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


def _expand_recurring_event(event: dict, rrule: str) -> list[dict]:
    rule = _parse_rrule(rrule)
    if rule.get("FREQ") != "WEEKLY":
        return [event]

    start = datetime.fromisoformat(event["starts_at"])
    end = datetime.fromisoformat(event["ends_at"])
    duration = end - start
    interval = int(rule.get("INTERVAL", "1"))
    weekdays = _rrule_weekdays(rule.get("BYDAY")) or [start.weekday()]
    until = _rrule_until(rule.get("UNTIL")) or (datetime.now() + timedelta(days=180))
    count = int(rule.get("COUNT", "0") or 0)
    window_start = datetime.now() - timedelta(days=30)
    window_end = datetime.now() + timedelta(days=180)
    hard_end = min(until, window_end)

    occurrences: list[dict] = []
    emitted = 0
    cursor = start
    while cursor <= hard_end:
        week_offset = ((cursor.date() - start.date()).days // 7)
        if week_offset % interval == 0 and cursor.weekday() in weekdays and cursor >= window_start:
            occurrence_start = cursor.replace(
                hour=start.hour,
                minute=start.minute,
                second=start.second,
                microsecond=start.microsecond,
            )
            occurrence_end = occurrence_start + duration
            occurrence = event.copy()
            occurrence["starts_at"] = occurrence_start.isoformat(timespec="minutes")
            occurrence["ends_at"] = occurrence_end.isoformat(timespec="minutes")
            occurrence["external_id"] = f"{event['external_id']}:{occurrence_start.isoformat(timespec='minutes')}"
            occurrences.append(occurrence)
            emitted += 1
            if count and emitted >= count:
                break
        cursor += timedelta(days=1)

    return occurrences or [event]


def _parse_rrule(value: str) -> dict[str, str]:
    rule: dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        rule[key.upper()] = raw_value
    return rule


def _rrule_weekdays(value: str | None) -> list[int]:
    if not value:
        return []
    return [
        WEEKDAY_INDEX[day]
        for day in value.split(",")
        if day in WEEKDAY_INDEX
    ]


def _rrule_until(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = _parse_datetime(value, "")
    if not parsed:
        return None
    return datetime.fromisoformat(parsed)


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
