"""
Secondary file: Alert Logic Implementation
Threshold-based alerting based on rainfall intensity.
"""
from datetime import datetime
GREEN_THRESHOLD = 10.0
YELLOW_THRESHOLD = 20.0
GREEN = "green"
YELLOW = "yellow"
RED = "red"
ALERT_LOG_FILE = "alert_log.txt"
def classify_alert(rainfall_mmh: float) -> str:
    """
    Classify rainfall intensity (mm/h) into alert level.
    Green: rainfall < 10 mm/h (Normal)
    Yellow: 10 <= rainfall < 20 mm/h (Moderate)
    Red: rainfall >= 20 mm/h (Heavy - ALERT)
    """
    if rainfall_mmh >= YELLOW_THRESHOLD:
        return RED
    elif rainfall_mmh >= GREEN_THRESHOLD:
        return YELLOW
    else:
        return GREEN
def format_alert_message(rainfall_mmh: float, level: str, city: str = "") -> str:
    """Return a human-readable warning message for dashboard display."""
    labels = {
        GREEN: "Normal",
        YELLOW: "Moderate",
        RED: "Heavy — ALERT",
    }
    label = labels.get(level, "Unknown")
    prefix = f"[{city}] " if city else ""
    return f"{prefix}[{label}] Current rainfall: {rainfall_mmh:.1f} mm/h"
def log_alert(rainfall_mmh: float, level: str, city: str = "") -> None:
    """
    Append an alert event to alert_log.txt with a timestamp.
    Only called for Red alerts.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    city_tag = f" | {city}" if city else ""
    message = f"[{timestamp}]{city_tag} {level.upper()} — Rainfall: {rainfall_mmh:.1f} mm/h\n"
    with open(ALERT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message)
def handle_alert(rainfall_mmh: float, city: str = "") -> dict:
    """
    Evaluate rainfall intensity, trigger alerts, and return structured result.
    Red alerts are automatically logged to alert_log.txt.
    
    Returns dict with keys: level, message, logged, timestamp.
    """
    level = classify_alert(rainfall_mmh)
    message = format_alert_message(rainfall_mmh, level, city)
    logged = False
    if level == RED:
        log_alert(rainfall_mmh, level, city)
        logged = True
    return {
        "level": level,
        "message": message,
        "logged": logged,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city": city,
    }