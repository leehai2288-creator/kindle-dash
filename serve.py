# -*- coding: utf-8 -*-
"""Máy chủ ảnh cho Kindle. Vẽ ảnh MỚI mỗi khi Kindle (hoặc trình duyệt) hỏi, nên giờ luôn đúng.
Chạy trên PC:      python serve.py            (hoặc python serve.py --demo)
Chạy trên Render:  tự đọc biến môi trường PORT.
"""
import http.server, os, socket, socketserver, sys, threading, time
import config, dash

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO = "--demo" in sys.argv
PORT = int(os.environ.get("PORT", config.PORT))
MIN_AGE = 45          # giây: hỏi dồn dập thì dùng lại ảnh vừa vẽ
_lock = threading.Lock()
_last = [0.0]

def fresh_image():
    with _lock:
        if time.time() - _last[0] > MIN_AGE or not os.path.exists(os.path.join(HERE, "dash.png")):
            dash.build(demo=DEMO)
            _last[0] = time.time()
            print(time.strftime("%H:%M:%S"), "đã vẽ lại dash.png", flush=True)

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/dash.png":
            try:
                fresh_image()
                with open(os.path.join(HERE, "dash.png"), "rb") as fh:
                    self._send(200, fh.read(), "image/png")
            except Exception as e:
                print("Lỗi khi vẽ:", e, flush=True)
                self._send(500, ("Loi: %s" % e).encode("utf-8"), "text/plain; charset=utf-8")
        else:
            self._send(200, b"Kindle dashboard OK. Anh o /dash.png", "text/plain; charset=utf-8")

class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

if __name__ == "__main__":
    try:
        fresh_image()
    except Exception as e:
        print("Chưa vẽ được lần đầu:", e, flush=True)
    print("=" * 60)
    print("Máy chủ ảnh đang chạy ở cổng %d. Địa chỉ trong mạng nhà:" % PORT)
    print("   http://%s:%d/dash.png" % (lan_ip(), PORT))
    print("Đóng cửa sổ này là dừng.")
    print("=" * 60, flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
