"""
risk_engine.py
---------------
Fuses (a) pest-detection confidence from images and (b) regional weather
forecast into a 0-100 early-warning risk score per pest species, using
weighted agronomy thresholds. This is the core "early warning" logic.

Usage:
    python risk_engine.py --lat 15.48 --lon 78.49 --pest aphid
    python risk_engine.py --lat 15.48 --lon 78.49 --pest aphid --confidence 0.82
"""

import argparse
from weather_api import get_weather

# Illustrative pest-favorability profiles.
# Each pest has an ideal temp/humidity/rainfall range under which it thrives.
# Calibrate these with local agri-extension data for production use.
PEST_PROFILES = {
    "aphid": {
        "temp_range": (20, 30),        # deg C
        "humidity_range": (60, 90),    # %
        "rain_sensitivity": "low",     # heavy rain suppresses aphids
        "description": "Aphids thrive in warm, humid conditions with low rainfall.",
    },
    "locust": {
        "temp_range": (25, 40),
        "humidity_range": (40, 70),
        "rain_sensitivity": "positive_lag",  # outbreaks follow rain + vegetation flush
        "description": "Locust swarms often follow rainfall events that green up vegetation.",
    },
    "fungal_vector_pest": {
        "temp_range": (18, 28),
        "humidity_range": (75, 100),
        "rain_sensitivity": "high",
        "description": "High humidity and recent rain favor fungal-associated pests.",
    },
    "whitefly": {
        "temp_range": (25, 35),
        "humidity_range": (50, 80),
        "rain_sensitivity": "low",
        "description": "Whiteflies favor hot, moderately humid, dry-spell conditions.",
    },
}


def _score_in_range(value, low, high):
    """Returns 0-1 favorability score: 1.0 inside range, decaying outside it."""
    if value is None:
        return 0.5
    if low <= value <= high:
        return 1.0
    span = high - low if high > low else 1
    dist = min(abs(value - low), abs(value - high))
    return max(0.0, 1.0 - dist / span)


def compute_weather_favorability(pest: str, forecast_day: dict) -> float:
    profile = PEST_PROFILES[pest]
    temp_avg = (forecast_day["temp_max"] + forecast_day["temp_min"]) / 2
    temp_score = _score_in_range(temp_avg, *profile["temp_range"])
    humidity_score = _score_in_range(forecast_day["humidity_max"], *profile["humidity_range"])

    rain = forecast_day["rainfall_mm"]
    if profile["rain_sensitivity"] == "high":
        rain_score = min(1.0, rain / 20)
    elif profile["rain_sensitivity"] == "positive_lag":
        rain_score = min(1.0, rain / 15)
    else:  # low sensitivity -> heavy rain suppresses pest
        rain_score = max(0.0, 1.0 - rain / 25)

    # weighted blend: temperature and humidity matter most
    favorability = 0.4 * temp_score + 0.35 * humidity_score + 0.25 * rain_score
    return favorability  # 0-1


def compute_risk(pest: str, lat: float, lon: float, detection_confidence: float = None) -> dict:
    if pest not in PEST_PROFILES:
        raise ValueError(f"Unknown pest '{pest}'. Options: {list(PEST_PROFILES)}")

    weather = get_weather(lat, lon, forecast_days=7)
    daily_scores = []
    for day in weather["forecast"]:
        fav = compute_weather_favorability(pest, day)
        daily_scores.append({"date": day["date"], "favorability": round(fav, 3)})

    # Weather risk = average favorability over next 7 days, weighted toward near-term
    weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05][:len(daily_scores)]
    weather_risk = sum(d["favorability"] * w for d, w in zip(daily_scores, weights)) / sum(weights)

    # Combine with image-based detection confidence, if available.
    # No detection yet -> weather-only "pre-emptive" early warning.
    if detection_confidence is not None:
        combined = 0.5 * weather_risk + 0.5 * detection_confidence
        basis = "weather forecast + confirmed image detection"
    else:
        combined = weather_risk
        basis = "weather forecast only (pre-emptive, no confirmed sighting yet)"

    risk_score = round(combined * 100, 1)

    if risk_score >= 70:
        level = "HIGH"
    elif risk_score >= 40:
        level = "MODERATE"
    else:
        level = "LOW"

    return {
        "pest": pest,
        "risk_score": risk_score,
        "risk_level": level,
        "basis": basis,
        "daily_weather_favorability": daily_scores,
        "profile_note": PEST_PROFILES[pest]["description"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--pest", required=True, choices=list(PEST_PROFILES.keys()))
    parser.add_argument("--confidence", type=float, default=None,
                         help="Optional image-detection confidence (0-1)")
    args = parser.parse_args()

    result = compute_risk(args.pest, args.lat, args.lon, args.confidence)
    print(f"Pest: {result['pest']}")
    print(f"Risk score: {result['risk_score']} ({result['risk_level']})")
    print(f"Basis: {result['basis']}")
    print(f"Note: {result['profile_note']}")
