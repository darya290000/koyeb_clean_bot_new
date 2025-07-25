import requests
import json
import time
import os

# دریافت مقادیر از متغیرهای محیطی
config = {
    "BOT_TOKEN": os.getenv("BOT_TOKEN"),
    "CHAT_ID": os.getenv("CHAT_ID")
}

def send_message(message):
    url = f"https://api.telegram.org/bot{config['BOT_TOKEN']}/sendMessage"
    data = {
        "chat_id": config["CHAT_ID"],
        "text": message
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error sending message:", e)

if __name__ == "__main__":
    send_message("✅ ربات ایچی‌موکو فعال شد و در حال اجراست...")
    while True:
        send_message("📈 سیگنال جدید: (مثال)")
        time.sleep(180)
