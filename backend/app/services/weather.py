import httpx

from app.config import DEFAULT_TIMEZONE, DRESDEN_LATITUDE, DRESDEN_LONGITUDE
from app.schemas import WeatherSummary


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def get_dresden_weather() -> WeatherSummary:
    params = {
        "latitude": DRESDEN_LATITUDE,
        "longitude": DRESDEN_LONGITUDE,
        "current": "temperature_2m,apparent_temperature,precipitation,rain,wind_speed_10m",
        "daily": "precipitation_probability_max",
        "timezone": DEFAULT_TIMEZONE,
        "forecast_days": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError:
        return WeatherSummary(
            temperature_c=8,
            feels_like_c=6,
            precipitation_probability=60,
            rain_mm=1.0,
            wind_kmh=18,
            condition="fallback: cool and possibly rainy",
        )

    current = payload.get("current", {})
    daily = payload.get("daily", {})
    rain_mm = float(current.get("rain") or current.get("precipitation") or 0)
    precipitation_probability = int((daily.get("precipitation_probability_max") or [0])[0] or 0)
    temperature = float(current.get("temperature_2m") or 0)
    wind = float(current.get("wind_speed_10m") or 0)

    if rain_mm > 0 or precipitation_probability >= 50:
        condition = "rain likely"
    elif temperature <= 5:
        condition = "cold"
    elif temperature >= 25:
        condition = "warm"
    elif wind >= 25:
        condition = "windy"
    else:
        condition = "mild"

    return WeatherSummary(
        temperature_c=temperature,
        feels_like_c=current.get("apparent_temperature"),
        precipitation_probability=precipitation_probability,
        rain_mm=rain_mm,
        wind_kmh=wind,
        condition=condition,
    )

