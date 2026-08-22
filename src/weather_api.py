"""
weather_api.py
--------------
Fetches current + short-term forecast weather for a farm/region using the
free Open-Meteo API (no API key required).

Usage:
    python weather_api.py --lat 15.48 --lon 78.49
"""

import argparse
import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(lat: float, lon: float, forecast_days: int = 7) -> dict:
    """
    Returns current conditions + daily forecast (temp, humidity, rainfall, wind)
    for the given coordinates.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                 "relative_humidity_2m_max,wind_speed_10m_max",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    forecast = []
    for i, date in enumerate(daily.get("time", [])):
        forecast.append({
            "date": date,
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "humidity_max": daily["relative_humidity_2m_max"][i],
            "rainfall_mm": daily["precipitation_sum"][i],
            "wind_max": daily["wind_speed_10m_max"][i],
        })

    return {
        "current": {
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_kmh": current.get("wind_speed_10m"),
        },
        "forecast": forecast,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    args = parser.parse_args()

    weather = get_weather(args.lat, args.lon)
    print("Current conditions:", weather["current"])
    print("\n7-day forecast:")
    for day in weather["forecast"]:
        print(f"  {day['date']}: {day['temp_min']}-{day['temp_max']}C, "
              f"humidity {day['humidity_max']}%, rain {day['rainfall_mm']}mm")
