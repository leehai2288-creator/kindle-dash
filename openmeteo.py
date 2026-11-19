# -*- coding: utf-8 -*-
"""Lấy dữ liệu thời tiết + AQI từ Open-Meteo (chỉ dùng thư viện chuẩn)."""
import json, random, time, urllib.error, urllib.parse, urllib.request
import config


def http_json(url, timeout=25, tries=4):
    """Tải JSON; gặp 429/5xx (máy chủ dùng chung bị giới hạn) thì chờ rồi thử lại."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kindle-dash-vn/1.0 (personal e-ink dashboard)"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except Exception as e:
            last = e
        print("Tải lỗi (%s), thử lại lần %d..." % (last, i + 1), flush=True)
        if i < tries - 1:
            time.sleep(2 * (i + 1) + random.random())
    raise last


def fetch_raw(tries=4):
    q = urllib.parse.urlencode({
        "latitude": config.LAT, "longitude": config.LON, "timezone": "Asia/Bangkok", "forecast_days": 4,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,precipitation_probability,uv_index",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,uv_index_max",
    }, safe=",")
    w = http_json("https://api.open-meteo.com/v1/forecast?" + q, tries=tries)
    aq = {}
    try:
        q2 = urllib.parse.urlencode({"latitude": config.LAT, "longitude": config.LON,
                                     "timezone": "Asia/Bangkok", "current": "us_aqi,pm2_5"}, safe=",")
        aq = http_json("https://air-quality-api.open-meteo.com/v1/air-quality?" + q2, tries=max(2, tries // 2)).get("current", {})
    except Exception as e:  # AQI hỏng thì vẫn có phần còn lại
        print("Không lấy được AQI:", e, flush=True)
    return w, aq
