"""
alert_system.py
-----------------
Turns a risk_engine result into a human-readable early-warning alert,
logs it to logs/alerts.log, and provides pluggable stubs for sending it
via email/SMS (wire in real credentials/providers for production).
"""

import os
import json
import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "alerts.log")

RECOMMENDED_ACTIONS = {
    "HIGH": "Inspect fields within 24-48 hours; consider preventive treatment "
            "and alert neighboring farms in the same weather zone.",
    "MODERATE": "Increase field monitoring frequency this week; prepare "
                "treatment supplies as a precaution.",
    "LOW": "Routine monitoring is sufficient; no immediate action needed.",
}


def build_alert_message(risk_result: dict, region_name: str = "your region") -> str:
    level = risk_result["risk_level"]
    action = RECOMMENDED_ACTIONS[level]
    return (
        f"[{level} RISK] {risk_result['pest'].upper()} outbreak risk in {region_name}: "
        f"{risk_result['risk_score']}/100.\n"
        f"Basis: {risk_result['basis']}.\n"
        f"{risk_result['profile_note']}\n"
        f"Recommended action: {action}"
    )


def log_alert(risk_result: dict, region_name: str = "your region"):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "region": region_name,
        "pest": risk_result["pest"],
        "risk_score": risk_result["risk_score"],
        "risk_level": risk_result["risk_level"],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def send_email_alert(message: str, to_address: str):
    """Stub: wire up SendGrid/SMTP here for production."""
    print(f"[EMAIL STUB] Would send to {to_address}:\n{message}\n")


def send_sms_alert(message: str, phone_number: str):
    """Stub: wire up Twilio here for production."""
    print(f"[SMS STUB] Would send to {phone_number}:\n{message}\n")


def dispatch_alert(risk_result: dict, region_name: str = "your region",
                    email: str = None, phone: str = None):
    message = build_alert_message(risk_result, region_name)
    log_alert(risk_result, region_name)

    if risk_result["risk_level"] in ("HIGH", "MODERATE"):
        if email:
            send_email_alert(message, email)
        if phone:
            send_sms_alert(message, phone)

    return message


if __name__ == "__main__":
    # Demo with a synthetic risk result
    demo_risk = {
        "pest": "aphid",
        "risk_score": 76.4,
        "risk_level": "HIGH",
        "basis": "weather forecast + confirmed image detection",
        "profile_note": "Aphids thrive in warm, humid conditions with low rainfall.",
    }
    msg = dispatch_alert(demo_risk, region_name="Nandyal, AP", email="farmer@example.com")
    print(msg)
