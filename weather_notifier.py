import os
import sys
import json
import urllib.request
import argparse
from datetime import datetime
from typing import List, Optional

# =========================
# DEFAULTS & CONFIG
# =========================
DEFAULT_LAT = "47.4979"
DEFAULT_LON = "19.0402"
DEFAULT_CITY = "Budapest"
DEFAULT_NAME = "Boss" # Default greeting name

# =========================
# HELPER FUNCTIONS
# =========================

def get_env_or_arg(arg_value: Optional[str], env_name: str, default: Optional[str] = None) -> str:
    """Gets the argument, falls back to env variable, then default."""
    value = arg_value or os.getenv(env_name) or default
    if value is None:
        print(f"❌ Error: Environment variable or parameter '{env_name}' is missing!")
        sys.exit(1)
    return value

def comfort_score(t_max: float, rain_prob: float, wind_max: float, uv: float, apparent_temp: float) -> int:
    """Calculates a 0-100 comfort index."""
    score = 100
    if rain_prob > 70: score -= 25
    elif rain_prob > 40: score -= 15
    if wind_max > 40: score -= 20
    elif wind_max > 25: score -= 10
    if uv > 8: score -= 10
    elif uv > 6: score -= 5
    if apparent_temp > 34: score -= 15
    elif apparent_temp > 30: score -= 5
    if apparent_temp < -5: score -= 20
    elif apparent_temp < 5: score -= 10
    return max(score, 0)

def outfit_for_temp(temp: Optional[float], tolerance_offset: int = 0) -> str:
    """Suggests an outfit, adjusted by your personal cold tolerance."""
    if temp is None:
        return "🤷 No data"
        
    # Adjust the perceived temperature based on how hot/cold you run
    adjusted_temp = temp + tolerance_offset

    if adjusted_temp < 5: return "🧥 Winter coat, beanie, scarf"
    if adjusted_temp < 12: return "🧥 Jacket / Coat"
    if adjusted_temp < 18: return "🧥 Sweater or light jacket"
    if adjusted_temp < 24: return "👕 T-shirt / Long-sleeve"
    return "🩳 Shorts, light summer clothes"

def weather_summary(t_max: float, rain_prob: float, wind_max: float, uv: float) -> str:
    """Generates a short, readable summary."""
    summary = []
    if t_max >= 28: summary.append("warm")
    elif t_max <= 10: summary.append("cold")
    else: summary.append("pleasant")

    if rain_prob > 60: summary.append("rainy")
    if wind_max > 30: summary.append("windy")
    if uv > 7: summary.append("very sunny")
    return " and ".join(summary)

def get_hourly_rain_message(hourly_times: List[str], hourly_rain: List[float]) -> str:
    """Finds the earliest hour with significant rain."""
    for time_str, rain in zip(hourly_times, hourly_rain):
        if rain >= 50:
            hour = time_str.split("T")[1][:5]
            return f"☂️ GRAB AN UMBRELLA! Heavy rain expected around {hour}."
    return "☀️ No umbrella needed today."

def get_temp_for_hour(hourly_times: List[str], hourly_temps: List[float], target_hour: int) -> Optional[float]:
    """Extracts the temperature for a specific commute hour."""
    for time_str, temp in zip(hourly_times, hourly_temps):
        dt = datetime.fromisoformat(time_str)
        if dt.hour == target_hour:
            return temp
    return None

# =========================
# MAIN LOGIC
# =========================

def main():
    parser = argparse.ArgumentParser(description="Send a personalized daily weather briefing via ntfy.")
    
    # Location Settings
    parser.add_argument("--lat", help=f"Latitude (default: {DEFAULT_LAT})")
    parser.add_argument("--lon", help=f"Longitude (default: {DEFAULT_LON})")
    parser.add_argument("--city", help=f"City name (default: {DEFAULT_CITY})")
    parser.add_argument("--channel", help="ntfy channel name (or use NTFY_CHANNEL env var)")
    
    # Personalization Settings
    parser.add_argument("--name", default=DEFAULT_NAME, help="Your name for the greeting")
    parser.add_argument("--morning", type=int, default=8, help="Your morning commute hour (0-23)")
    parser.add_argument("--afternoon", type=int, default=17, help="Your afternoon commute hour (0-23)")
    parser.add_argument("--evening", type=int, default=21, help="Your evening plans hour (0-23)")
    parser.add_argument("--tolerance", type=int, default=0, 
                        help="Cold tolerance: +5 if you run hot, -5 if you get cold easily")

    args = parser.parse_args()

    lat = args.lat or DEFAULT_LAT
    lon = args.lon or DEFAULT_LON
    city = args.city or DEFAULT_CITY
    ntfy_channel = get_env_or_arg(args.channel, "NTFY_CHANNEL")

    # HOZZÁADVA: sunshine_duration a daily API paraméterekhez
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,apparent_temperature,relative_humidity_2m"
        f"&hourly=temperature_2m,precipitation_probability"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,uv_index_max,sunshine_duration"
        f"&timezone=auto"
    )

    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())

        current = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        c_temp = current.get("temperature_2m", 0)
        a_temp = current.get("apparent_temperature", 0)
        hum = current.get("relative_humidity_2m", 0)

        t_max = daily.get("temperature_2m_max", [0])[0]
        t_min = daily.get("temperature_2m_min", [0])[0]
        rain_p = daily.get("precipitation_probability_max", [0])[0]
        wind_m = daily.get("wind_speed_10m_max", [0])[0]
        uv_idx = daily.get("uv_index_max", [0])[0]
        
        # Napsütéses órák kiszámítása (másodpercből órába)
        sun_seconds = daily.get("sunshine_duration", [0])[0]
        sun_hours = sun_seconds / 3600

        h_times = hourly.get("time", [])[:24]
        h_temps = hourly.get("temperature_2m", [])[:24]
        h_rain = hourly.get("precipitation_probability", [])[:24]

        score = comfort_score(t_max, rain_p, wind_m, uv_idx, a_temp)
        summary = weather_summary(t_max, rain_p, wind_m, uv_idx)
        rain_msg = get_hourly_rain_message(h_times, h_rain)

        m_temp = get_temp_for_hour(h_times, h_temps, args.morning)
        a_temp_day = get_temp_for_hour(h_times, h_temps, args.afternoon)
        e_temp = get_temp_for_hour(h_times, h_temps, args.evening)

        # FRISSÍTETT FIGYELMEZTETÉSEK
        warns = []
        if uv_idx > 7: 
            warns.append("🕶️ SUNGLASSES & sunscreen needed! (High UV)")
        elif sun_hours > 7: 
            warns.append("🕶️ SUNGLASSES recommended! (Lots of sunshine today)")
            
        if a_temp > 32: warns.append("🥵 Very hot & humid! Stay hydrated.")
        if wind_m > 40: warns.append("🌪️ Very windy (don't spend time on your hair).")
        elif wind_m > 25: warns.append("🌬️ It's going to be breezy.")
        if t_min < 10 and t_max > 22: warns.append("🧅 Dress in layers! (Cold morning, warm afternoon).")

        warn_text = "\n".join([f"• {w}" for w in warns]) if warns else "• No special warnings today."

        # Constructing the personalized message
        message = f"""
🌤️ DAILY BRIEFING - {city}

Good morning, {args.name}! ☕
Today will be {summary}.
{rain_msg}

⚠️ HEADS UP:
{warn_text}

👗 WHAT TO WEAR?
🌅 Morning ({args.morning}:00): {m_temp}°C -> {outfit_for_temp(m_temp, args.tolerance)}
🌞 Afternoon ({args.afternoon}:00): {a_temp_day}°C -> {outfit_for_temp(a_temp_day, args.tolerance)}
🌙 Evening ({args.evening}:00): {e_temp}°C -> {outfit_for_temp(e_temp, args.tolerance)}

--- 📊 THE NERDY DETAILS ---
🌡️ Right now: {c_temp}°C (Feels like: {a_temp}°C)
📈 High: {t_max}°C | 📉 Low: {t_min}°C
☔ Rain chance: {rain_p}% | 💧 Humidity: {hum}%
🌬️ Wind max: {wind_m} km/h | ☀️ UV: {uv_idx} | 🕒 Sun: {round(sun_hours, 1)} hrs
😎 Comfort Score: {score}/100
"""

        ntfy_url = f"https://ntfy.sh/{ntfy_channel}"
        req = urllib.request.Request(
            ntfy_url,
            data=message.strip().encode("utf-8"),
            method="POST"
        )
        req.add_header("Title", f"Daily Briefing ({city})")
        req.add_header("Priority", "4")
        req.add_header("Tags", "partly_sunny,coffee")

        urllib.request.urlopen(req)
        print(f"✅ Personalized briefing sent to {args.name} for {city}!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
