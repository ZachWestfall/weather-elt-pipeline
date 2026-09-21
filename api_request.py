import os
import requests

API_KEY = os.environ.get("WEATHERSTACK_API_KEY")
QUERY = os.environ.get("WEATHERSTACK_QUERY", "New York")
UNITS = os.environ.get("WEATHERSTACK_UNITS", "m")

API_URL = "https://api.weatherstack.com/current"


def _require_key():
    """Fail fast with a clear message rather than sending an unauthenticated request."""
    if not API_KEY:
        raise RuntimeError(
            "WEATHERSTACK_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return API_KEY

def fetch_data():
    print("Attempting to recieve weather data from weatherstack API")
    try:
        response = requests.get(
            API_URL,
            params={"access_key": _require_key(), "query": QUERY, "units": UNITS},
            timeout=10,
        )
        response.raise_for_status()
        print("API response recieved")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occured: {e}")
        return False

def mock_fetch_data():
    return {'request': {'type': 'City', 'query': 'New York, United States of America', 'language': 'en', 'unit': 'm'}, 'location': {'name': 'New York', 'country': 'United States of America', 'region': 'New York', 'lat': '40.714', 'lon': '-74.006', 'timezone_id': 'America/New_York', 'localtime': '2026-05-03 16:18', 'localtime_epoch': 1777825080, 'utc_offset': '-4.0'}, 'current': {'observation_time': '08:18 PM', 'temperature': 13, 'weather_code': 116, 'weather_icons': ['https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0002_sunny_intervals.png'], 'weather_descriptions': ['Partly cloudy'], 'astro': {'sunrise': '05:52 AM', 'sunset': '07:55 PM', 'moonrise': '10:22 PM', 'moonset': '06:28 AM', 'moon_phase': 'Waning Gibbous', 'moon_illumination': 98}, 'air_quality': {'co': '210.85', 'no2': '23.25', 'o3': '68', 'so2': '3.65', 'pm2_5': '8.85', 'pm10': '9.75', 'us-epa-index': '1', 'gb-defra-index': '1'}, 'wind_speed': 29, 'wind_degree': 309, 'wind_dir': 'NW', 'pressure': 1012, 'precip': 0, 'humidity': 26, 'cloudcover': 75, 'feelslike': 11, 'uv_index': 3, 'visibility': 16, 'is_day': 'yes'}}