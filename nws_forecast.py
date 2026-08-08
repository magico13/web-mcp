"""
Fetches and parses NWS DWML XML from forecast.weather.gov/MapClick.php
and returns a concise text summary for LLM consumption.
"""
import xml.etree.ElementTree as ET
import requests


def get_nws_forecast(lat: float, lon: float) -> str:
    """
    Fetch the NWS forecast for the given coordinates and return a
    plain-text summary with period names, datetimes, and worded forecasts.
    """
    url = f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}&FcstType=dwml"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return parse_dwml(response.text)


def parse_dwml(xml_text: str) -> str:
    """Parse a DWML XML string and return a formatted forecast summary."""
    root = ET.fromstring(xml_text)

    lines: list[str] = []

    # --- Current observations ---
    obs_data = root.find("./data[@type='current observations']")
    if obs_data is not None:
        area = obs_data.findtext("./location/area-description", "")
        obs_time_el = obs_data.find("./time-layout/start-valid-time")
        obs_time = obs_time_el.get("period-name", obs_time_el.text) if obs_time_el is not None else ""
        params = obs_data.find("./parameters")
        obs_parts: list[str] = []
        if params is not None:
            apparent = params.findtext("./temperature[@type='apparent']/value")
            if apparent:
                obs_parts.append(f"Feels Like: {apparent}°F")
            dew = params.findtext("./temperature[@type='dew point']/value")
            if dew:
                obs_parts.append(f"Dew Point: {dew}°F")
            humidity = params.findtext("./humidity[@type='relative']/value")
            if humidity:
                obs_parts.append(f"Humidity: {humidity}%")
            summary_el = params.find("./weather/weather-conditions[@weather-summary]")
            if summary_el is not None:
                obs_parts.append(f"Weather: {summary_el.get('weather-summary')}")
            visibility_el = params.find("./weather/weather-conditions/value/visibility")
            if visibility_el is not None:
                obs_parts.append(f"Visibility: {visibility_el.text} {visibility_el.get('units', '')}")
            wind_dir = params.findtext("./direction[@type='wind']/value")
            wind_sustained = params.findtext("./wind-speed[@type='sustained']/value")
            wind_gust = params.findtext("./wind-speed[@type='gust']/value")
            if wind_sustained:
                wind_str = f"Wind: {_degrees_to_direction(wind_dir)} at {wind_sustained} kt"
                if wind_gust:
                    wind_str += f" (gust {wind_gust} kt)"
                obs_parts.append(wind_str)
            pressure = params.findtext("./pressure[@type='barometer']/value")
            if pressure:
                obs_parts.append(f"Pressure: {pressure} inHg")
        if area:
            lines.append(f"## Current Conditions — {area} ({obs_time})")
        else:
            lines.append(f"## Current Conditions ({obs_time})")
        lines.append(", ".join(obs_parts))
        lines.append("")

    # --- Forecast ---
    fcst_data = root.find("./data[@type='forecast']")
    if fcst_data is None:
        if not lines:
            return "No forecast data found."
        return "\n".join(lines)

    location_desc = fcst_data.findtext("./location/description", "")
    lat_el = fcst_data.find("./location/point")
    coord_str = ""
    if lat_el is not None:
        coord_str = f" ({lat_el.get('latitude')}, {lat_el.get('longitude')})"

    lines.append(f"## 7-Day Forecast — {location_desc}{coord_str}")
    lines.append("")

    # Build a map from layout-key → list of (period_name, start_time_str)
    time_layouts: dict[str, list[tuple[str, str]]] = {}
    for layout in fcst_data.findall("./time-layout"):
        key_el = layout.find("layout-key")
        if key_el is None:
            continue
        key = key_el.text or ""
        periods: list[tuple[str, str]] = []
        for svt in layout.findall("start-valid-time"):
            period_name = svt.get("period-name", "")
            periods.append((period_name, svt.text or ""))
        time_layouts[key] = periods

    # Find the wordedForecast element
    worded = fcst_data.find("./parameters/wordedForecast")
    if worded is None:
        lines.append("No worded forecast available.")
        return "\n".join(lines)

    layout_key = worded.get("time-layout", "")
    periods = time_layouts.get(layout_key, [])
    texts = [el.text or "" for el in worded.findall("text")]

    for i, text in enumerate(texts):
        if i < len(periods):
            period_name, start_time = periods[i]
            # Format the datetime nicely
            dt_str = _fmt_iso(start_time)
            header = f"{period_name} ({dt_str})"
        else:
            header = f"**Period {i + 1}**"
        lines.append(f"{header}: {text.strip()}")

    return "\n".join(lines)


def _fmt_iso(iso: str) -> str:
    """Format an ISO 8601 datetime string to a compact readable form."""
    try:
        # Strip the offset so fromisoformat works on all Python versions
        # e.g. "2026-03-15T18:00:00-04:00" → "Mar 15"
        from datetime import datetime, timezone, timedelta
        # Parse offset manually for python < 3.11 compat
        if len(iso) > 6 and iso[-6] in ("+", "-"):
            sign = 1 if iso[-6] == "+" else -1
            h, m = int(iso[-5:-3]), int(iso[-2:])
            tz = timezone(timedelta(hours=sign * h, minutes=sign * m))
            dt = datetime.fromisoformat(iso[:-6]).replace(tzinfo=tz)
        else:
            dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %-d").strip()
    except Exception:
        return iso


def _degrees_to_direction(degrees_str: str | None) -> str:
    if degrees_str is None:
        return "?"
    try:
        d = float(degrees_str)
    except ValueError:
        return degrees_str
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = round(d / 45) % 8
    return dirs[idx]


if __name__ == "__main__":
    # Quick smoke test
    print(get_nws_forecast(43.18, -77.8))
