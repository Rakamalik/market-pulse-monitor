import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
FLASK_URL = "http://localhost:5000"

def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    r = requests.get(f"{BASE_URL}/getUpdates", params=params)
    return r.json()

def send_photo(chat_id, photo_bytes, caption=""):
    requests.post(f"{BASE_URL}/sendPhoto", files={
        "photo": ("rrg.png", photo_bytes, "image/png")
    }, data={"chat_id": chat_id, "caption": caption})

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": chat_id, "text": text
    })

def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/rrg"):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "Usage: /rrg BBCA BBRI BMRI")
            return
        tickers = ",".join(parts[1:])
        send_message(chat_id, f"Generating RRG for {tickers}...")
        r = requests.get(f"{FLASK_URL}/rrg?tickers={tickers}")
        if r.status_code == 200:
            send_photo(chat_id, r.content, f"📊 Psychological RRG\n{tickers}")
        else:
            send_message(chat_id, f"Error: {r.text}")

    elif text.startswith("/sentiment"):
        send_message(chat_id, "Fetching sentiment...")
        requests.get(f"{FLASK_URL}/notify")

    elif text.startswith("/fetch"):
        r = requests.get(f"{FLASK_URL}/fetch")
        send_message(chat_id, r.json().get("message", "Done"))

def main():
    print("Bot started...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
