from app.schemas import DailyBriefing


def answer_student_question(
    question: str,
    briefing: DailyBriefing,
    groceries: list[dict],
    expenses: dict,
    budget: dict,
) -> dict:
    normalized = question.strip().lower()
    intent = _detect_intent(normalized)

    if intent == "schedule":
        answer = _schedule_answer(briefing)
        suggestions = ["What should I wear today?", "What should I eat today?"]
    elif intent == "outfit":
        answer = _outfit_answer(briefing)
        suggestions = ["What should I pack?", "Do I need an umbrella?"]
    elif intent == "meals":
        answer = _meal_answer(briefing)
        suggestions = ["What groceries should I buy?", "How much did I spend this month?"]
    elif intent == "shopping":
        answer = _shopping_answer(briefing, groceries)
        suggestions = ["What is expiring soon?", "What should I cook for dinner?"]
    elif intent == "budget":
        answer = _budget_answer(expenses, budget)
        suggestions = ["How can I save money?", "What groceries should I buy?"]
    elif intent == "weather":
        answer = _weather_answer(briefing)
        suggestions = ["What should I wear today?", "Do I need an umbrella?"]
    elif intent == "help":
        answer = (
            "I can help with your schedule, outfit, meals, groceries, shopping list, weather, and monthly food budget."
        )
        suggestions = ["What is my schedule today?", "What should I eat after football?"]
    else:
        answer = _daily_summary_answer(briefing)
        suggestions = ["What should I wear today?", "What should I eat today?", "What should I buy?"]

    return {
        "answer": answer,
        "intent": intent,
        "suggestions": suggestions,
        "source": "jarvis_local",
    }


def _detect_intent(question: str) -> str:
    if not question or any(word in question for word in ["hello", "hi", "help", "start", "open jarvis"]):
        return "help"
    if any(word in question for word in ["schedule", "calendar", "lecture", "class", "today plan"]):
        return "schedule"
    if any(word in question for word in ["wear", "outfit", "clothes", "jacket", "umbrella", "rain"]):
        return "outfit"
    if any(word in question for word in ["eat", "cook", "meal", "breakfast", "lunch", "dinner", "football"]):
        return "meals"
    if any(word in question for word in ["grocery", "groceries", "shopping", "buy", "aldi", "rewe", "lidl", "expiring"]):
        return "shopping"
    if any(word in question for word in ["spend", "spent", "budget", "expense", "saving", "save money"]):
        return "budget"
    if any(word in question for word in ["weather", "temperature", "wind", "cold", "hot"]):
        return "weather"
    return "daily_summary"


def _daily_summary_answer(briefing: DailyBriefing) -> str:
    schedule = " ".join(briefing.schedule[:2]) if briefing.schedule else "You have no schedule items saved for today."
    meals = ", ".join(f"{meal}: {name}" for meal, name in briefing.meals.items())
    alerts = " ".join(briefing.alerts[:2]) if briefing.alerts else "No urgent alerts."
    return f"{briefing.greeting} {schedule} Meals are {meals}. {alerts}"


def _schedule_answer(briefing: DailyBriefing) -> str:
    if not briefing.schedule:
        return "You have no schedule items saved for today."
    return "Today your schedule is: " + " ".join(briefing.schedule)


def _outfit_answer(briefing: DailyBriefing) -> str:
    if not briefing.outfit_details:
        return "I need more wardrobe items before I can choose accurately."
    items = []
    reasons = []
    for item in briefing.outfit_details:
        if item.name.startswith("no jacket"):
            reasons.append(item.reason)
            continue
        items.append(item.name)
        if item.reason:
            reasons.append(f"{item.name}: {item.reason}.")
    answer = f"Wear {', '.join(items)}." if items else "Keep the outfit light today."
    if reasons:
        answer += " " + " ".join(reasons[:3])
    return answer


def _meal_answer(briefing: DailyBriefing) -> str:
    if briefing.meal_details:
        parts = [
            f"{item.meal}: {item.name}, about {item.prep_minutes} minutes, for {item.focus}."
            for item in briefing.meal_details
        ]
        return "Here is your food plan. " + " ".join(parts)
    return "Your meals are " + ", ".join(f"{meal}: {name}" for meal, name in briefing.meals.items())


def _shopping_answer(briefing: DailyBriefing, groceries: list[dict]) -> str:
    shopping = " ".join(briefing.shopping) if briefing.shopping else "Your shopping list is empty."
    expiring = [item["name"] for item in groceries if item.get("expires_on")][:4]
    if expiring:
        shopping += f" Watch these groceries first: {', '.join(expiring)}."
    return shopping


def _budget_answer(expenses: dict, budget: dict) -> str:
    total = expenses.get("total", 0)
    remaining = budget.get("remaining", 0)
    message = budget.get("message", "Budget status is unavailable.")
    suggestions = expenses.get("suggestions", [])
    saving_tip = f" {suggestions[0]}" if suggestions else ""
    return f"You spent {total:.2f} euros this month. You have {remaining:.2f} euros left. {message}{saving_tip}"


def _weather_answer(briefing: DailyBriefing) -> str:
    weather = briefing.weather
    return (
        f"It is {weather.temperature_c:.1f} degrees in Dresden with {weather.condition}. "
        f"Rain chance is {weather.precipitation_probability} percent and wind is {weather.wind_kmh:.1f} kilometers per hour."
    )
