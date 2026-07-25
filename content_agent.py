import os
import requests
from google import genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FLASK_URL = "http://localhost:5000"

def get_sentiment():
    r = requests.get(f"{FLASK_URL}/sentiment")
    return r.json()

def generate_drafts(sentiment_data):
    client = genai.Client(api_key=GEMINI_KEY)
    
    today = datetime.now().strftime("%d %b %Y")
    dominant = sentiment_data[0]['sentiment'] if sentiment_data else "Neutral"
    total = sum(s['total'] for s in sentiment_data)
    
    sentiment_str = "\n".join([
        f"{s['sentiment']}: {s['total']} berita ({round(s['total']/total*100)}%)"
        for s in sentiment_data
    ])

    prompt = f"""
Kamu adalah content creator investasi syariah bernama Endecapi.
Tone: santai, campur Indo-Inggris, data-first, tidak menggurui.
Filosofi: sajikan data jujur, bukan rekomendasi. Keputusan di tangan user.

Data sentiment pasar syariah hari ini ({today}):
{sentiment_str}
Dominant: {dominant}

Buatkan 3 draft post berbeda:

DRAFT 1 - X/Twitter (maks 260 karakter, data-first):
Mulai dengan angka/data, akhiri dengan insight singkat.
Wajib ada disclaimer ringan. Tambah hashtag #SahamSyariah #Endecapi

DRAFT 2 - Threads (lebih panjang, conversational, 3-5 paragraf pendek):
Ceritakan apa yang data katakan. Tambah konteks kenapa ini penting.
Tone lebih santai, seperti ngobrol sama teman.

DRAFT 3 - Casual/relatable (bisa meme format, joke ringan, atau POV):
Ringan, relatable, tidak harus soal data. 
Tapi tetap ada nilai edukasi di dalamnya.

Format output:
DRAFT1:
[isi]

DRAFT2:
[isi]

DRAFT3:
[isi]
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def send_to_telegram(drafts):
    token = TELEGRAM_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    message = f"📝 *Draft Konten Endecapi Hari Ini*\n\n{drafts}\n\n---\nReply angka untuk approve (1/2/3) atau 'edit: ...' untuk revisi"
    
    requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    })

def run():
    print("Generating content drafts...")
    sentiment = get_sentiment()
    drafts = generate_drafts(sentiment)
    send_to_telegram(drafts)
    print("Drafts sent to Telegram!")

if __name__ == "__main__":
    run()
