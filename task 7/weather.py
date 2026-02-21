# weather.py
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from pprint import pprint

# 🔑 Load API key from .env
load_dotenv()  # loads .env in current folder
API_KEY = os.getenv("OPENWEATHER_API_KEY")
print("API Key loaded:", API_KEY)



if not API_KEY:
    print("Please set OPENWEATHER_API_KEY in your .env or environment.")
    raise SystemExit(1)

from datetime import datetime, timezone   # <-- upar import update karein

def _ts_to_local(ts, tz_shift):
    """Convert unix timestamp to local time string using timezone shift (in seconds)."""
    return datetime.fromtimestamp(ts + tz_shift, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def get_weather(city, units="metric"):
    """
    Returns a dict with parsed weather for a given city (e.g. "Karachi,PK" or "London").
    units: "metric" (Celsius), "imperial" (Fahrenheit), or "standard" (Kelvin)
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": units}

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": str(e)}

    data = resp.json()
    # API returns cod != 200 on errors (e.g., 404)
    if data.get("cod") != 200 and str(data.get("cod")) != "200":
        return {"error": data.get("message", "Unknown error from API")}

    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})
    sys = data.get("sys", {})
    tz_shift = data.get("timezone", 0)  # seconds

    result = {
        "city": f"{data.get('name')}, {sys.get('country')}",
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "temp_min": main.get("temp_min"),
        "temp_max": main.get("temp_max"),
        "pressure": main.get("pressure"),
        "humidity": main.get("humidity"),
        "condition": weather.get("description"),
        "wind_speed": wind.get("speed"),
        "sunrise_local": _ts_to_local(sys.get("sunrise"), tz_shift) if sys.get("sunrise") else None,
        "sunset_local": _ts_to_local(sys.get("sunset"), tz_shift) if sys.get("sunset") else None,
        "raw": data
    }
    return result

if __name__ == "__main__":
    city = input("Enter city (e.g. Karachi or Karachi,PK): ").strip()
    units = input("Units - metric/imperial/standard (default metric): ").strip() or "metric"
    out = get_weather(city, units=units)
    if "error" in out:
        print("Error:", out["error"])
    else:
        print(f"\nWeather in {out['city']}:")
        unit_sym = "°C" if units == "metric" else ("°F" if units == "imperial" else "K")
        print(f"Temperature: {out['temperature']} {unit_sym} (Feels like: {out['feels_like']}{unit_sym})")
        print(f"Condition: {out['condition'].capitalize()}")
        print(f"Humidity: {out['humidity']}%")
        print(f"Pressure: {out['pressure']} hPa")
        print(f"Wind speed: {out['wind_speed']} m/s")
        print(f"Sunrise: {out['sunrise_local']}")
        print(f"Sunset : {out['sunset_local']}")
