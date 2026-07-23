from datetime import date

from app.schemas import DailyBriefing, WeatherSummary
from app.services.assistant import answer_student_question


def _briefing(schedule: list[str]) -> DailyBriefing:
    return DailyBriefing(
        greeting="Good morning, I am Jarvis.",
        weather=WeatherSummary(
            temperature_c=20,
            precipitation_probability=10,
            rain_mm=0,
            wind_kmh=5,
            condition="clear",
        ),
        schedule=schedule,
        outfit=[],
        meals={"breakfast": "oats"},
        shopping=[],
        alerts=[],
    )


def test_schedule_answer_uses_tomorrow_label() -> None:
    result = answer_student_question(
        "what is my schedule tomorrow",
        _briefing(["09:00-10:00: Lecture"]),
        groceries=[],
        expenses={"total": 0, "suggestions": []},
        budget={"remaining": 100, "message": "ok"},
        target_day=date(2026, 7, 24),
    )

    assert result["intent"] == "schedule"
    assert result["answer"].startswith("Tomorrow your schedule is")


def test_empty_tomorrow_schedule_is_clear() -> None:
    result = answer_student_question(
        "what is my schedule tomorrow",
        _briefing([]),
        groceries=[],
        expenses={"total": 0, "suggestions": []},
        budget={"remaining": 100, "message": "ok"},
        target_day=date(2026, 7, 24),
    )

    assert result["answer"] == "You have no schedule items saved for tomorrow."
