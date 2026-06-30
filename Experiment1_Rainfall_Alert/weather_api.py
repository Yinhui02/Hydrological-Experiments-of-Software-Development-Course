"""
Secondary file: API Integration
Fetches current weather data from OpenWeatherMap API for multiple cities.
"""
import requests
import time
from typing import Optional
CITIES = ["Beijing", "Xi'an", "Zhengzhou", "Shanghai", "Kunming"]
API_KEY = "YOUR_API_KEY_HERE" #  YOUR_API_KEY_HERE
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
def get_weather_data(city: str) -> dict:
    """Y
    Fetch current weather data for a given city from OpenWeatherMap API.
    Returns parsed JSON response.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
    }
    response = None
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise requests.exceptions.RequestException(
            "API request timed out after 10 seconds."
        )
    except requests.exceptions.HTTPError as e:
        if response is not None:
            status = response.status_code
            if status == 401:
                raise ValueError("Invalid API key. Please check your API key.")
            elif status == 404:
                raise ValueError(f"City '{city}' not found.")
            else:
                raise ValueError(f"HTTP {status}: {e}")
        else:
            raise ValueError(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.RequestException(
            "Failed to connect to the API. Check your network connection."
        )
    try:
        data = response.json()
    except ValueError:
        raise ValueError("API returned non-JSON response.")
    if "main" not in data:
        raise ValueError("Unexpected API response format — 'main' key missing.")
    return data
def extract_rainfall(data: dict) -> float:
    """
    Extract rainfall intensity (mm/h) from API response.
    OpenWeatherMap provides rain volume in 'rain' object:
    - rain.1h: mm over last hour (directly mm/h)
    - rain.3h: mm over last 3 hours (divided by 3 for mm/h)
    Returns rainfall intensity in mm/h (0.0 if no rain data).
    """
    rain = data.get("rain", {})
    if "1h" in rain:
        return float(rain["1h"])
    elif "3h" in rain:
        return float(rain["3h"]) / 3.0
    return 0.0
def get_city_weather(city: str) -> Optional[dict]:
    """
    High-level function: fetch and process weather data for one city.
    Returns dict with city, temperature, humidity, rainfall, description, timestamp.
    """
    try:
        data = get_weather_data(city)
    except Exception as e:
        print(f"Error fetching {city}: {e}")
        return None
    rainfall = extract_rainfall(data)
    return {
        "city": city,
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "rainfall": rainfall,
        "description": data["weather"][0]["description"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
def get_all_cities_weather() -> list:
    """Fetch weather data for all configured cities."""
    results = []
    for city in CITIES:
        data = get_city_weather(city)
        if data:
            results.append(data)
    return results
def get_beijing_rainfall() -> dict:
    """
    Convenience wrapper (backward-compatible): fetch Beijing rainfall.
    Returns dict with rain_1h and rain_3h keys.
    """
    data = get_weather_data("Beijing")
    rain = data.get("rain", {})
    return {
        "rain_1h": rain.get("1h", 0.0),
        "rain_3h": rain.get("3h", 0.0),
    }
if __name__ == "__main__":
    for city_data in get_all_cities_weather():
        if city_data:
            print(f"{city_data['city']}: {city_data['rainfall']:.1f} mm/h, "
                  f"{city_data['temperature']:.1f}°C, {city_data['description']}")