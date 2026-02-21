from flask import Flask, render_template, request
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

app = Flask(__name__)

def _ts_to_local(ts, tz_shift):
    return datetime.fromtimestamp(ts + tz_shift, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def get_weather(city, units="metric"):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": units}

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        return {"error": str(e)}

    data = resp.json()
    if data.get("cod") != 200 and str(data.get("cod")) != "200":
        return {"error": data.get("message", "Unknown error")}

    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})
    sys = data.get("sys", {})
    tz_shift = data.get("timezone", 0)

    return {
        "city": f"{data.get('name')}, {sys.get('country')}",
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "condition": weather.get("description"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),
        "sunrise": _ts_to_local(sys.get("sunrise"), tz_shift),
        "sunset": _ts_to_local(sys.get("sunset"), tz_shift),
        "units": units
    }

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = None
    error = None
    if request.method == "POST":
        city = request.form.get("city")
        units = request.form.get("units", "metric")
        weather_data = get_weather(city, units)
        if "error" in weather_data:
            error = weather_data["error"]
            weather_data = None
    return render_template("index.html", weather=weather_data, error=error)

if __name__ == "__main__":
    app.run(debug=True)
