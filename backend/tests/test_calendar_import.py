from app.services.calendar_import import parse_ics_events


def test_parse_weekly_recurring_event_expands_occurrences() -> None:
    raw_ics = """
BEGIN:VCALENDAR
BEGIN:VEVENT
UID:lecture-1
SUMMARY:Software Management Lecture
DTSTART:20260701T092000
DTEND:20260701T105000
RRULE:FREQ=WEEKLY;UNTIL=20260801T000000;BYDAY=WE
LOCATION:TU Dresden
END:VEVENT
END:VCALENDAR
"""

    events = parse_ics_events(raw_ics)
    starts = [event["starts_at"] for event in events]

    assert "2026-07-22T09:20" in starts
    assert "2026-07-29T09:20" in starts
    assert all(event["external_id"].startswith("lecture-1:") for event in events)


def test_parse_non_recurring_event_keeps_uid() -> None:
    raw_ics = """
BEGIN:VCALENDAR
BEGIN:VEVENT
UID:exam-1
SUMMARY:Exam
DTSTART:20260724T100000
DTEND:20260724T110000
END:VEVENT
END:VCALENDAR
"""

    events = parse_ics_events(raw_ics)

    assert len(events) == 1
    assert events[0]["external_id"] == "exam-1"
