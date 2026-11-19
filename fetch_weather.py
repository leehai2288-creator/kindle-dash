# -*- coding: utf-8 -*-
"""Chạy trong GitHub Actions: lấy thời tiết rồi ghi weather.json."""
import json, time
import openmeteo

w, aq = openmeteo.fetch_raw(tries=6)
with open("weather.json", "w", encoding="utf-8") as fh:
    json.dump({"fetched": time.time(), "w": w, "aq": aq}, fh, ensure_ascii=False)
print("Đã ghi weather.json")
