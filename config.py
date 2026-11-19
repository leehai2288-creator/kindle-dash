# -*- coding: utf-8 -*-
# Chỉnh các thông số ở đây rồi chạy lại.

PLACE = "HÀ ĐÔNG · HÀ NỘI"      # dòng tiêu đề góc trên bên trái
LAT, LON = 20.9719, 105.7788     # tọa độ Hà Đông
UTC_OFFSET_HOURS = 7             # giờ Việt Nam

REFRESH_MINUTES = 5              # bao lâu vẽ lại ảnh một lần (Kindle cũng nên tải với chu kỳ này)
FOOTER_LEFT = ""                 # ví dụ: tên quán của bạn

# Hướng xoay ảnh để khớp màn hình Kindle (đặt Kindle nằm ngang).
# 90  = logo "kindle" ở bên TRÁI khi nhìn (giống ảnh mẫu của bạn)
# 270 = logo "kindle" ở bên PHẢI
ROTATE_DEG = 90

PORT = 8080                      # cổng máy chủ ảnh trên PC
