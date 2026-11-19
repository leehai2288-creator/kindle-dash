# -*- coding: utf-8 -*-
"""Vẽ bảng thông tin cho Kindle Paperwhite 3 (1072x1448), kiểu ảnh ngang 1448x1072 rồi xoay.

Dùng:  python dash.py            -> lấy dữ liệu thật, ghi dash.png
       python dash.py --demo     -> dùng dữ liệu mẫu (không cần mạng), ghi dash.png
"""
import json, os, random, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont

import amlich
import config

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1448, 1072          # khung vẽ (ngang)
BLACK, DARK, MID, LIGHT, WHITE = 0, 55, 140, 205, 255

WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

PROVERBS = [
    "Học thầy không tày học bạn.",
    "Có công mài sắt, có ngày nên kim.",
    "Ăn quả nhớ kẻ trồng cây.",
    "Uống nước nhớ nguồn.",
    "Đi một ngày đàng, học một sàng khôn.",
    "Lá lành đùm lá rách.",
    "Nước chảy đá mòn.",
    "Kiến tha lâu cũng đầy tổ.",
    "Có chí thì nên.",
    "Tốt gỗ hơn tốt nước sơn.",
    "Thất bại là mẹ thành công.",
    "Nhất nước, nhì phân, tam cần, tứ giống.",
    "Làm ruộng ăn cơm nằm, chăn tằm ăn cơm đứng.",
    "Gần mực thì đen, gần đèn thì rạng.",
    "Một cây làm chẳng nên non, ba cây chụm lại nên hòn núi cao.",
    "Cẩn tắc vô áy náy.",
]

# ---------------------------------------------------------------- phông chữ
_fc = {}
def F(kind, size):
    key = (kind, size)
    if key not in _fc:
        name = {"reg": "Inter-Regular.otf", "semi": "Inter-SemiBold.otf",
                "bold": "Inter-Bold.otf", "serif": "Lora.ttf"}[kind]
        _fc[key] = ImageFont.truetype(os.path.join(HERE, "fonts", name), size)
    return _fc[key]

def tw(d, s, f):
    return d.textlength(s, font=f)

def T(d, x, y, s, f, fill=BLACK, anchor="ls"):
    d.text((x, y), s, font=f, fill=fill, anchor=anchor)

def fit(d, s, kind, size, maxw, minsize=14):
    while size > minsize and tw(d, s, F(kind, size)) > maxw:
        size -= 1
    return F(kind, size)

def spaced(d, x, y, s, f, gap=2, fill=BLACK):
    for ch in s:
        T(d, x, y, ch, f, fill)
        x += tw(d, ch, f) + gap
    return x

def hline(d, x0, x1, y, w=3, fill=BLACK):
    d.rectangle([x0, y, x1, y + w - 1], fill=fill)

def dotted(d, x0, x1, y, fill=MID):
    x = x0
    while x < x1:
        d.rectangle([x, y, x + 3, y + 1], fill=fill)
        x += 8

# ---------------------------------------------------------------- biểu tượng thời tiết
def cloud(d, x, y, s, fill=BLACK):
    """Đám mây vẽ trong ô vuông kích thước s, góc trên-trái (x, y)."""
    d.ellipse([x + 0.12 * s, y + 0.42 * s, x + 0.46 * s, y + 0.78 * s], fill=fill)
    d.ellipse([x + 0.30 * s, y + 0.22 * s, x + 0.68 * s, y + 0.74 * s], fill=fill)
    d.ellipse([x + 0.52 * s, y + 0.38 * s, x + 0.90 * s, y + 0.78 * s], fill=fill)
    d.rectangle([x + 0.28 * s, y + 0.56 * s, x + 0.72 * s, y + 0.78 * s], fill=fill)

def sun(d, cx, cy, r, fill=BLACK):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    import math
    for i in range(8):
        a = i * math.pi / 4
        d.line([cx + math.cos(a) * r * 1.45, cy + math.sin(a) * r * 1.45,
                cx + math.cos(a) * r * 1.95, cy + math.sin(a) * r * 1.95], fill=fill, width=max(2, int(r / 4)))

def icon(d, kind, x, y, s):
    if kind == "sun":
        sun(d, x + s / 2, y + s / 2, s * 0.22)
    elif kind == "partly":
        sun(d, x + s * 0.34, y + s * 0.36, s * 0.15)
        d.ellipse([x + 0.30 * s, y + 0.36 * s, x + 0.58 * s, y + 0.70 * s], fill=WHITE)
        cloud(d, x + 0.10 * s, y + 0.12 * s, s * 0.95)
    elif kind == "cloud":
        cloud(d, x, y, s)
    elif kind in ("rain", "storm"):
        cloud(d, x, y - s * 0.12, s)
        for i in range(3):
            xx = x + s * (0.28 + 0.2 * i)
            d.line([xx + s * 0.07, y + s * 0.66, xx - s * 0.03, y + s * 0.92], fill=BLACK, width=max(2, int(s / 12)))
        if kind == "storm":
            d.polygon([(x + s * 0.52, y + s * 0.6), (x + s * 0.40, y + s * 0.82), (x + s * 0.50, y + s * 0.82),
                       (x + s * 0.44, y + s * 1.0), (x + s * 0.64, y + s * 0.74), (x + s * 0.53, y + s * 0.74)], fill=BLACK)
    elif kind == "fog":
        for i in range(4):
            yy = y + s * (0.25 + 0.17 * i)
            d.line([x + s * 0.1, yy, x + s * 0.9, yy], fill=BLACK, width=max(2, int(s / 12)))

def weather_desc(code):
    """WMO weather code -> (mô tả tiếng Việt, kiểu biểu tượng)"""
    table = {0: ("Trời quang", "sun"), 1: ("Ít mây", "partly"), 2: ("Có mây", "partly"), 3: ("Nhiều mây", "cloud"),
             45: ("Sương mù", "fog"), 48: ("Sương mù", "fog"),
             51: ("Mưa phùn", "rain"), 53: ("Mưa phùn", "rain"), 55: ("Mưa phùn", "rain"),
             56: ("Mưa phùn lạnh", "rain"), 57: ("Mưa phùn lạnh", "rain"),
             61: ("Mưa nhẹ", "rain"), 63: ("Mưa vừa", "rain"), 65: ("Mưa to", "rain"),
             66: ("Mưa lạnh", "rain"), 67: ("Mưa lạnh", "rain"),
             80: ("Mưa rào nhẹ", "rain"), 81: ("Mưa rào", "rain"), 82: ("Mưa rào to", "rain"),
             95: ("Dông", "storm"), 96: ("Dông, mưa đá", "storm"), 99: ("Dông, mưa đá", "storm")}
    return table.get(code, ("Không rõ", "cloud"))

def aqi_info(v):
    if v <= 50: return "TỐT", "Không khí trong lành."
    if v <= 100: return "TRUNG BÌNH", "Nhóm nhạy cảm lưu ý."
    if v <= 150: return "KÉM", "Nhóm nhạy cảm nên hạn chế ra ngoài."
    if v <= 200: return "XẤU", "Nên đeo khẩu trang khi ra ngoài."
    if v <= 300: return "RẤT XẤU", "Hạn chế ra ngoài, đóng cửa sổ."
    return "NGUY HẠI", "Ở trong nhà."

def hum_info(h):
    if h < 30: return "KHÔ", "Độ ẩm thấp, nhớ uống nước."
    if h <= 85: return "ỔN", "Độ ẩm dễ chịu."
    return "ẨM", "Độ ẩm cao, dễ bí."

def uv_label(v):
    if v < 3: return "Thấp"
    if v < 6: return "Trung bình"
    if v < 8: return "Cao"
    if v < 11: return "Rất cao"
    return "Cực cao"

# ---------------------------------------------------------------- dữ liệu
def http_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "kindle-dash-vn/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

_RAW = {"t": 0.0, "w": None, "aq": None}
RAW_TTL = 600  # giây: dữ liệu thời tiết thô được dùng lại tối đa 10 phút

def fetch_raw():
    q = urllib.parse.urlencode({
        "latitude": config.LAT, "longitude": config.LON, "timezone": "Asia/Bangkok", "forecast_days": 4,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,precipitation_probability,uv_index",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,uv_index_max",
    }, safe=",")
    w = http_json("https://api.open-meteo.com/v1/forecast?" + q)
    aq = {}
    try:
        q2 = urllib.parse.urlencode({"latitude": config.LAT, "longitude": config.LON,
                                     "timezone": "Asia/Bangkok", "current": "us_aqi,pm2_5"}, safe=",")
        aq = http_json("https://air-quality-api.open-meteo.com/v1/air-quality?" + q2).get("current", {})
    except Exception as e:  # AQI hỏng thì vẫn vẽ phần còn lại
        print("Không lấy được AQI:", e)
    return w, aq

def process(w, aq, now):
    cur = w["current"]
    ht = w["hourly"]["time"]
    today = now.strftime("%Y-%m-%d")
    nxt = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:00")
    i0 = next((i for i, t in enumerate(ht) if t >= nxt), 0)
    hours = []
    for i in range(i0, min(i0 + 6, len(ht))):
        hours.append({"t": ht[i][-5:], "temp": w["hourly"]["temperature_2m"][i],
                      "pop": w["hourly"]["precipitation_probability"][i] or 0,
                      "uv": w["hourly"]["uv_index"][i] or 0})
    today_idx = [i for i, t in enumerate(ht) if t.startswith(today)]
    peak = max(today_idx, key=lambda i: w["hourly"]["uv_index"][i] or 0) if today_idx else None
    dd = w["daily"]
    # ngày dự báo = 3 ngày sau hôm nay (tìm theo ngày để không lệch khi qua nửa đêm)
    di = next((i for i, t in enumerate(dd["time"]) if t > today), 1)
    days = []
    for i in range(di, min(di + 3, len(dd["time"]))):
        days.append({"date": dd["time"][i], "code": dd["weather_code"][i],
                     "lo": dd["temperature_2m_min"][i], "hi": dd["temperature_2m_max"][i]})
    ti = dd["time"].index(today) if today in dd["time"] else 0
    return {
        "temp": cur["temperature_2m"], "feels": cur["apparent_temperature"], "hum": cur["relative_humidity_2m"],
        "wind": cur["wind_speed_10m"], "code": cur["weather_code"],
        "hi": dd["temperature_2m_max"][ti], "lo": dd["temperature_2m_min"][ti],
        "hours": hours,
        "uv_peak": round(w["hourly"]["uv_index"][peak]) if peak is not None else None,
        "uv_peak_time": ht[peak][-5:] if peak is not None else None,
        "days": days,
        "aqi": aq.get("us_aqi"), "pm25": aq.get("pm2_5"),
    }

def fetch_live(now):
    import time as _t
    ts = _t.time()
    if _RAW["w"] is None or ts - _RAW["t"] > RAW_TTL:
        try:
            w, aq = fetch_raw()
            _RAW.update(t=ts, w=w, aq=aq)
        except Exception:
            if _RAW["w"] is None:
                raise
            print("Dùng lại dữ liệu cũ trong bộ nhớ")
    return process(_RAW["w"], _RAW["aq"], now)

def demo_data(now):
    """Dữ liệu mẫu giống ảnh bạn gửi (dùng để xem thử, không cần mạng)."""
    base = now.date()
    pops = [98, 96, 94, 94, 95, 96]
    temps = [26, 25, 24, 23, 23, 22]
    uvs = [1, 0, 0, 0, 0, 0]
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    hours = [{"t": (start + timedelta(hours=i)).strftime("%H:00"), "temp": temps[i], "pop": pops[i], "uv": uvs[i]}
             for i in range(6)]
    codes = [81, 3, 3]
    los, his = [16, 16, 16], [22, 21, 23]
    days = [{"date": (base + timedelta(days=i + 1)).isoformat(), "code": codes[i], "lo": los[i], "hi": his[i]}
            for i in range(3)]
    return {"temp": 26.5, "feels": 30.9, "hum": 80, "wind": 6.0, "code": 1, "hi": 28, "lo": 22,
            "hours": hours, "uv_peak": 6, "uv_peak_time": "12:00", "days": days, "aqi": 79, "pm25": 24.8}

def get_data(now, demo=False):
    if demo:
        return demo_data(now), False
    cache = os.path.join(HERE, "cache.json")
    try:
        data = fetch_live(now)
        with open(cache, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        return data, False
    except Exception as e:
        print("Không lấy được dữ liệu mới:", e)
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as fh:
                return json.load(fh), True
        raise

# ---------------------------------------------------------------- vẽ
def num(v, nd=0):
    return ("%.*f" % (nd, v)).replace("-0", "0") if v is not None else "--"

def render(data, now, stale=False):
    im = Image.new("L", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    M = 48
    lc0, lc1 = M, 680           # cột trái
    rc0, rc1 = 740, W - M       # cột phải

    # ---- tiêu đề
    T(d, M, 78, config.PLACE, F("bold", 34))
    T(d, W - M, 78, "Cập nhật: %s%s" % (now.strftime("%H:%M"), " (dữ liệu cũ)" if stale else ""), F("semi", 30), anchor="rs")
    hline(d, M, W - M, 100, 4)
    d.rectangle([700, 124, 702, 830], fill=BLACK)

    # ---- đồng hồ lớn
    clock = now.strftime("%H:%M")
    T(d, lc0 - 6, 318, clock, fit(d, clock, "bold", 250, lc1 - lc0 + 6))

    # ---- ngày dương + tiết khí
    li = amlich.lunar_info(now.date())
    wd = WEEKDAYS[now.weekday()].upper()
    T(d, lc0, 378, "%s, %s" % (wd, now.strftime("%d/%m/%Y")), F("semi", 29))
    chip = "TIẾT KHÍ: " + li["tiet_khi"].upper()
    cf = F("bold", 21)
    cw = tw(d, chip, cf) + 24
    d.rectangle([lc0, 398, lc0 + cw, 434], fill=BLACK)
    T(d, lc0 + 12, 424, chip, cf, WHITE)

    # ---- âm lịch
    ax = 428
    am = "Âm lịch: %02d/%02d%s" % (li["day"], li["month"], " (nhuận)" if li["leap"] else "")
    T(d, ax, 378, am, F("bold", 32))
    hline(d, ax, lc1, 392, 2)
    for k, (lab, val) in enumerate([("Năm", li["year_cc"]), ("Tháng", li["month_cc"]), ("Ngày", li["day_cc"])]):
        y = 424 + k * 34
        x = ax + 4
        T(d, x, y, "• %s: " % lab, F("reg", 26))
        T(d, x + tw(d, "• %s: " % lab, F("reg", 26)), y, val, F("bold", 26))

    # ---- thanh đếm ngày (mùng 1, rằm)
    d.rectangle([lc0, 512, lc1, 566], outline=BLACK, width=2)
    hx, hy = lc0 + 22, 522
    d.polygon([(hx, hy), (hx + 22, hy), (hx + 11, hy + 17)], fill=BLACK)
    d.polygon([(hx + 11, hy + 17), (hx, hy + 34), (hx + 22, hy + 34)], outline=BLACK, fill=WHITE)
    d.line([hx - 3, hy, hx + 25, hy], fill=BLACK, width=3)
    d.line([hx - 3, hy + 34, hx + 25, hy + 34], fill=BLACK, width=3)
    m1, rm = li["to_mung1"], li["to_ram"]
    parts = [("Còn ", False), (str(m1), True), (" ngày tới Mùng 1 · ", False), (str(rm), True), (" ngày tới Rằm", False)]
    if rm == 0:
        parts = [("Hôm nay là ", False), ("Rằm", True), (" · còn ", False), (str(m1), True), (" ngày tới Mùng 1", False)]
    if m1 == 0:
        parts = [("Hôm nay là ", False), ("Mùng 1", True), (" · ", False), (str(rm), True), (" ngày tới Rằm", False)]
    x = lc0 + 62
    for s, b in parts:
        f = F("bold" if b else "reg", 26)
        T(d, x, 549, s, f)
        x += tw(d, s, f)

    # ---- AQI và độ ẩm
    def box(x0, x1, title, value, unit, tag, frac, l1, l2):
        d.rectangle([x0, 592, x1, 826], outline=BLACK, width=3)
        T(d, x0 + 16, 628, title, F("bold", 22))
        hline(d, x0 + 16, x1 - 16, 640, 2)
        vf = F("bold", 68)
        T(d, x0 + 16, 712, value, vf)
        vx = x0 + 16 + tw(d, value, vf) + 6
        if unit:
            T(d, vx, 712, unit, F("bold", 40))
            vx += tw(d, unit, F("bold", 40)) + 6
        tf = F("bold", 19)
        tgw = tw(d, tag, tf) + 20
        d.rectangle([vx + 6, 676, vx + 6 + tgw, 708], outline=BLACK, width=2)
        T(d, vx + 16, 699, tag, tf)
        bx0, bx1 = x0 + 16, x1 - 16
        d.rectangle([bx0, 734, bx1, 752], outline=BLACK, width=2, fill=WHITE)
        d.rectangle([bx0, 734, bx0 + int((bx1 - bx0) * max(0, min(1, frac))), 752], fill=BLACK)
        T(d, x0 + 16, 782, l1, fit(d, l1, "reg", 22, x1 - x0 - 30), MID if False else DARK)
        T(d, x0 + 16, 812, l2, fit(d, l2, "reg", 22, x1 - x0 - 30), DARK)

    if data.get("aqi") is not None:
        tag, tip = aqi_info(data["aqi"])
        box(lc0, 348, "AQI", num(data["aqi"]), "", tag, min(1, data["aqi"] / 300.0),
            "PM2.5: %s µg/m³" % num(data.get("pm25"), 1), tip)
    else:
        box(lc0, 348, "AQI", "--", "", "N/A", 0, "Chưa có dữ liệu", "")
    htag, htip = hum_info(data["hum"])
    box(380, lc1, "ĐỘ ẨM", num(data["hum"]), "%", htag, data["hum"] / 100.0, htip, "")

    # ---- nhiệt độ hiện tại
    tf = F("bold", 92)
    tt = "%s°C" % num(data["temp"], 1)
    T(d, rc0, 232, tt, tf)
    sx = rc0 + tw(d, tt, tf) + 24
    d.rectangle([sx, 142, sx + 2, 238], fill=BLACK)
    bx = sx + 20
    bl = [("Cảm nhận: ", "%s°" % num(data["feels"], 1)), ("Độ ẩm: ", "%s%%" % num(data["hum"])),
          ("Gió: ", "%s km/h" % num(data["wind"], 1))]
    for k, (a, b) in enumerate(bl):
        y = 170 + k * 34
        T(d, bx, y, "• " + a, F("reg", 25))
        T(d, bx + tw(d, "• " + a, F("reg", 25)), y, b, F("bold", 25))

    desc, ik = weather_desc(data["code"])
    icon(d, ik, rc0, 262, 50)
    T(d, rc0 + 64, 304, "%s (Cao %s° · Thấp %s°)" % (desc, num(data["hi"]), num(data["lo"])), F("semi", 31))

    # ---- mưa và UV theo giờ
    spaced(d, rc0, 366, "MƯA & UV THEO GIỜ", F("bold", 22), 2)
    tx0, tx1, ty0, ty1 = rc0, rc1, 384, 580
    colw = (tx1 - tx0) / 6.0
    d.rectangle([tx0, ty0, tx1, ty1], outline=BLACK, width=2)
    for i in range(1, 6):
        x = int(tx0 + colw * i)
        d.line([x, ty0, x, ty1], fill=BLACK, width=2)
    for i, h in enumerate(data["hours"][:6]):
        cx = tx0 + colw * i + colw / 2
        T(d, cx, ty0 + 38, h["t"], F("semi", 24), anchor="ms")
        T(d, cx, ty0 + 78, "%s°C" % num(h["temp"]), F("bold", 32), anchor="ms")
        T(d, cx, ty0 + 108, "Mưa %d%%" % round(h["pop"]), F("reg", 20), anchor="ms")
        bx0, bx1 = int(cx - 40), int(cx + 40)
        d.rectangle([bx0, ty0 + 122, bx1, ty0 + 136], outline=BLACK, width=2, fill=WHITE)
        d.rectangle([bx0, ty0 + 122, bx0 + int(80 * h["pop"] / 100.0), ty0 + 136], fill=BLACK)
        d.rectangle([int(cx - 34), ty0 + 150, int(cx + 34), ty0 + 184], outline=BLACK, width=2)
        T(d, cx, ty0 + 175, "UV %d" % round(h["uv"]), F("semi", 22), anchor="ms")
    d.rectangle([rc0, 604, rc0 + 14, 618], fill=BLACK)
    T(d, rc0 + 22, 620, "Thanh = xác suất mưa", F("reg", 21))
    if data.get("uv_peak") is not None:
        T(d, rc1, 620, "UV hôm nay: đỉnh %d lúc %s · %s" % (data["uv_peak"], data["uv_peak_time"], uv_label(data["uv_peak"])),
          F("reg", 21), anchor="rs")

    # ---- dự báo 3 ngày
    spaced(d, rc0, 676, "DỰ BÁO 3 NGÀY", F("bold", 22), 2)
    for k, day in enumerate(data["days"][:3]):
        y = 728 + k * 52
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        label = "%s (%s)" % (WEEKDAYS[dt.weekday()], dt.strftime("%d/%m"))
        T(d, rc0, y, label + " · ", F("semi", 27))
        x = rc0 + tw(d, label + " · ", F("semi", 27))
        desc, ik = weather_desc(day["code"])
        icon(d, ik, x, y - 30, 38)
        T(d, x + 46, y, desc, F("semi", 27))
        T(d, rc1, y, "%s° — %s°" % (num(day["lo"]), num(day["hi"])), F("bold", 27), anchor="rs")
        dotted(d, rc0, rc1, y + 14)

    # ---- tục ngữ
    hline(d, M, W - M, 872, 3)
    q = PROVERBS[now.timetuple().tm_yday % len(PROVERBS)]
    qs = "“%s”" % q
    qf = fit(d, qs, "serif", 50, W - 2 * M - 40)
    T(d, W / 2, 948, qs, qf, anchor="ms")
    T(d, W / 2, 992, "— Tục ngữ Việt Nam", F("semi", 23), anchor="ms")
    hline(d, M, W - M, 1010, 3)

    # ---- chân trang
    T(d, M, 1050, config.FOOTER_LEFT, F("semi", 24))
    T(d, W - M, 1050, "Tự động cập nhật mỗi %d phút" % config.REFRESH_MINUTES, F("reg", 22), anchor="rs")
    return im

def to_kindle(im):
    """Xoay và chuyển thành PNG xám 8-bit 1072x1448."""
    k = im.rotate(config.ROTATE_DEG, expand=True).convert("L")
    # 16 mức xám như màn hình e-ink thật -> file PNG nhỏ hơn (tiết kiệm băng thông khi tải mỗi phút)
    return k.point([min(255, int(round(v / 17.0)) * 17) for v in range(256)])

def now_vn():
    return datetime.now(timezone(timedelta(hours=config.UTC_OFFSET_HOURS))).replace(tzinfo=None)

def build(out="dash.png", demo=False, fixed_now=None, save_landscape=None):
    now = fixed_now or now_vn()
    data, stale = get_data(now, demo)
    im = render(data, now, stale)
    if save_landscape:
        im.save(save_landscape)
    k = to_kindle(im)
    tmp = os.path.join(HERE, out + ".tmp")
    k.save(tmp, format="PNG", optimize=True, compress_level=9)
    os.replace(tmp, os.path.join(HERE, out))
    return k.size

if __name__ == "__main__":
    demo = "--demo" in sys.argv
    print("Đã vẽ:", build(demo=demo, save_landscape=os.path.join(HERE, "preview_landscape.png")))
