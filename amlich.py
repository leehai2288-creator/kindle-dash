# -*- coding: utf-8 -*-
"""Âm lịch Việt Nam (múi giờ UTC+7), can-chi và tiết khí.
Thuật toán thiên văn của Hồ Ngọc Đức (https://www.informatik.uni-leipzig.de/~duc/amlich/)."""
import math
from datetime import date, timedelta

PI = math.pi
TZ = 7.0

CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

# 24 tiết khí, chỉ số i ứng với kinh độ mặt trời i*15 độ (0 = Xuân phân)
TIET_KHI = ["Xuân phân", "Thanh minh", "Cốc vũ", "Lập hạ", "Tiểu mãn", "Mang chủng",
            "Hạ chí", "Tiểu thử", "Đại thử", "Lập thu", "Xử thử", "Bạch lộ",
            "Thu phân", "Hàn lộ", "Sương giáng", "Lập đông", "Tiểu tuyết", "Đại tuyết",
            "Đông chí", "Tiểu hàn", "Đại hàn", "Lập xuân", "Vũ thủy", "Kinh trập"]


def _int(x):
    return int(math.floor(x))


def jd_from_date(dd, mm, yy):
    a = _int((14 - mm) / 12.0)
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jd = dd + _int((153 * m + 2) / 5.0) + 365 * y + _int(y / 4.0) - _int(y / 100.0) + _int(y / 400.0) - 32045
    if jd < 2299161:
        jd = dd + _int((153 * m + 2) / 5.0) + 365 * y + _int(y / 4.0) - 32083
    return jd


def _new_moon(k):
    T = k / 1236.85
    T2, T3 = T * T, T * T * T
    dr = PI / 180
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    c1 = (0.1734 - 0.000393 * T) * math.sin(M * dr) + 0.0021 * math.sin(2 * dr * M)
    c1 -= 0.4068 * math.sin(Mpr * dr) - 0.0161 * math.sin(dr * 2 * Mpr)
    c1 -= 0.0004 * math.sin(dr * 3 * Mpr)
    c1 += 0.0104 * math.sin(dr * 2 * F) - 0.0051 * math.sin(dr * (M + Mpr))
    c1 -= 0.0074 * math.sin(dr * (M - Mpr)) - 0.0004 * math.sin(dr * (2 * F + M))
    c1 -= 0.0004 * math.sin(dr * (2 * F - M)) + 0.0006 * math.sin(dr * (2 * F + Mpr))
    c1 += 0.0010 * math.sin(dr * (2 * F - Mpr)) + 0.0005 * math.sin(dr * (2 * Mpr + M))
    if T < -11:
        dt = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
    else:
        dt = -0.000278 + 0.000265 * T + 0.000262 * T2
    return jd1 + c1 - dt


def sun_longitude(jdn):
    """Kinh độ mặt trời (radian, 0..2π) tại JD (UT)."""
    T = (jdn - 2451545.0) / 36525
    T2 = T * T
    dr = PI / 180
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
    DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(dr * M)
    DL += (0.019993 - 0.000101 * T) * math.sin(dr * 2 * M) + 0.000290 * math.sin(dr * 3 * M)
    L = (L0 + DL) * dr
    return L - PI * 2 * _int(L / (PI * 2))


def _sun_long_idx(day_number, tz=TZ):
    # 0..11 (mỗi cung 30 độ), tính tại 0h giờ địa phương
    return _int(sun_longitude(day_number - 0.5 - tz / 24.0) / PI * 6)


def _new_moon_day(k, tz=TZ):
    return _int(_new_moon(k) + 0.5 + tz / 24.0)


def _lunar_month11(yy, tz=TZ):
    off = jd_from_date(31, 12, yy) - 2415021
    k = _int(off / 29.530588853)
    nm = _new_moon_day(k, tz)
    if _sun_long_idx(nm, tz) >= 9:
        nm = _new_moon_day(k - 1, tz)
    return nm


def _leap_month_offset(a11, tz=TZ):
    k = _int((a11 - 2415021.076998695) / 29.530588853 + 0.5)
    i = 1
    arc = _sun_long_idx(_new_moon_day(k + i, tz), tz)
    while True:
        last = arc
        i += 1
        arc = _sun_long_idx(_new_moon_day(k + i, tz), tz)
        if not (arc != last and i < 14):
            break
    return i - 1


def solar_to_lunar(d, tz=TZ):
    """date -> (ngày âm, tháng âm, năm âm, có phải tháng nhuận)"""
    dd, mm, yy = d.day, d.month, d.year
    day_number = jd_from_date(dd, mm, yy)
    k = _int((day_number - 2415021.076998695) / 29.530588853)
    month_start = _new_moon_day(k + 1, tz)
    if month_start > day_number:
        month_start = _new_moon_day(k, tz)
    a11 = _lunar_month11(yy, tz)
    b11 = a11
    if a11 >= month_start:
        lunar_year = yy
        a11 = _lunar_month11(yy - 1, tz)
    else:
        lunar_year = yy + 1
        b11 = _lunar_month11(yy + 1, tz)
    lunar_day = day_number - month_start + 1
    diff = _int((month_start - a11) / 29)
    leap = 0
    lunar_month = diff + 11
    if b11 - a11 > 365:
        leap_off = _leap_month_offset(a11, tz)
        if diff >= leap_off:
            lunar_month = diff + 10
            if diff == leap_off:
                leap = 1
    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1
    return lunar_day, lunar_month, lunar_year, leap


def can_chi_year(lunar_year):
    return "%s %s" % (CAN[(lunar_year + 6) % 10], CHI[(lunar_year + 8) % 12])


def can_chi_month(lunar_month, lunar_year):
    return "%s %s" % (CAN[(lunar_year * 12 + lunar_month + 3) % 10], CHI[(lunar_month + 1) % 12])


def can_chi_day(d):
    jd = jd_from_date(d.day, d.month, d.year)
    return "%s %s" % (CAN[(jd + 9) % 10], CHI[(jd + 1) % 12])


def tiet_khi(d, tz=TZ):
    """Tiết khí đang có hiệu lực vào ngày d (tính tại 12h trưa địa phương)."""
    jd = jd_from_date(d.day, d.month, d.year)
    lon = sun_longitude(jd - tz / 24.0)  # 12h trưa địa phương = jd - tz/24 (UT)
    idx = _int(lon / (PI / 12))
    return TIET_KHI[idx % 24]


def days_until_lunar_day(d, target, tz=TZ):
    """Số ngày từ d tới ngày âm 'target' kế tiếp (target=1: mùng 1, 15: rằm). Hôm nay đúng ngày đó -> 0."""
    for n in range(0, 32):
        if solar_to_lunar(d + timedelta(days=n), tz)[0] == target:
            return n
    return None


def lunar_info(d):
    ld, lm, ly, leap = solar_to_lunar(d)
    return {
        "day": ld, "month": lm, "year": ly, "leap": leap,
        "year_cc": can_chi_year(ly),
        "month_cc": can_chi_month(lm, ly),
        "day_cc": can_chi_day(d),
        "tiet_khi": tiet_khi(d),
        "to_mung1": days_until_lunar_day(d + timedelta(days=1), 1) + 1 if ld != 1 else 0,
        "to_ram": days_until_lunar_day(d, 15),
    }


if __name__ == "__main__":
    print(lunar_info(date.today()))
