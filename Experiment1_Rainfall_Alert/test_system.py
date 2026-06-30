"""
Testing & Validation Script
Verifies the rainfall monitoring system works correctly.
"""
import os
import sys
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
print("=" * 60)
print("RAINFALL MONITORING SYSTEM — VALIDATION REPORT")
print("=" * 60)
# --- 1. Test API Integration (weather_api.py) ---
print("\n[1] API Integration Test (weather_api.py)")
print("-" * 40)
exec(open("weather_api.py", encoding="utf-8").read())
all_data = get_all_cities_weather()
print(f"  Cities fetched: {len(all_data)}/{len(CITIES)}")
for d in all_data:
    print(f"    {d['city']:10s} | Rain: {d['rainfall']:.2f} mm/h  | "
          f"Temp: {d['temperature']:.1f}C  | {d['description']}")
# --- 2. Test Alert Logic (alert.py) ---
print("\n[2] Alert Threshold Test (alert.py)")
print("-" * 40)
exec(open("alert.py", encoding="utf-8").read())
if os.path.exists(ALERT_LOG_FILE):
    os.remove(ALERT_LOG_FILE)
threshold_tests = [
    (3.0, GREEN,  "Below 10 mm/h"),
    (9.9, GREEN,  "Below 10 mm/h (boundary)"),
    (10.0, YELLOW, "Exactly 10 mm/h"),
    (15.0, YELLOW, "Between 10-20 mm/h"),
    (19.9, YELLOW, "Below 20 mm/h (boundary)"),
    (20.0, RED,   "Exactly 20 mm/h"),
    (25.0, RED,   "Above 20 mm/h"),
    (50.0, RED,   "Heavy rain"),
]
passed = 0
for rain, expected, desc in threshold_tests:
    result = handle_alert(rain, "TestCity")
    level = result["level"]
    ok = "OK" if level == expected else "FAIL"
    if ok == "OK":
        passed += 1
    print(f"  {ok:4s} | {rain:5.1f} mm/h -> {level:6s} (expected {expected:6s}) | {desc}")
print(f"\n  Threshold tests: {passed}/{len(threshold_tests)} passed")
# --- 3. Check log file timestamps ---
print("\n[3] Log File Timestamp Check")
print("-" * 40)
if os.path.exists(ALERT_LOG_FILE):
    with open(ALERT_LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    print(f"  Log entries: {len(lines)}")
    for line in lines:
        has_timestamp = line.startswith("[") and "]" in line
        print(f"  {'VALID' if has_timestamp else 'INVALID'} | {line.strip()}")
else:
    print("  WARNING: No log file found after red alerts.")
# --- 4. Physical Reasonableness Validation ---
print("\n[4] Physical Reasonableness Check")
print("-" * 40)
for d in all_data:
    rf = d["rainfall"]
    temp = d["temperature"]
    issues = []
    if rf < 0:
        issues.append("Negative rainfall")
    if rf > 200:
        issues.append("Extreme rainfall > 200 mm/h (check for error)")
    if temp < -30:
        issues.append("Temperature below -30C (unlikely in China)")
    if temp > 50:
        issues.append("Temperature above 50C (unlikely in China)")
    
    status = "REASONABLE" if not issues else f"ISSUES: {', '.join(issues)}"
    print(f"  {d['city']:10s} | rf={rf:.1f} temp={temp:.1f}C -> {status}")
# --- 5. Summary ---
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  API: {len(all_data)}/{len(CITIES)} cities responsive")
print(f"  Thresholds: {passed}/{len(threshold_tests)} tests passed")
print(f"  Log file: {'Created' if os.path.exists(ALERT_LOG_FILE) else 'Missing'}")
print(f"  Dashboard: streamlit run dashboard.py")
print(f"  Dashboard URL: http://localhost:8501")
print("=" * 60)
# Clean up test log
os.remove(ALERT_LOG_FILE)