# =========================
# 1. IMPORT
# =========================
from google import genai as google_genai
from flask import Flask, jsonify, request
import feedparser
import psycopg2
import time
import os
import requests

# =========================
# 2. INIT APP
# =========================
app = Flask(__name__)

# =========================
# 3. DATABASE CONFIG
# =========================
DB_CONFIG = {
    "host": "db",
    "database": "devopsdb",
    "user": "devops",
    "password": "password"
}

# =========================
# SENTIMENT ANALYSIS
# =========================
def analyze_sentiment(text):
    text = text.lower()
    fear_words = ["crash", "turun", "jual", "anjlok", "drop", "fall", "decline", "bearish", "loss", "sell", "melemah", "tertekan", "koreksi", "terpuruk", "jeblok"]
    greed_words = ["naik", "profit", "beli", "rally", "surge", "gain", "bullish", "buy", "high", "menguat", "melonjak", "rekor", "optimis", "terbang"]
    hope_words = ["stabil", "recover", "rebound", "stable", "positive", "growth", "potential", "pulih", "harapan", "prospek", "potensi"]
    panic_words = ["kolaps", "bangkrut", "panik", "crash", "collapse", "bankrupt", "panic", "crisis", "plunge", "hancur", "ambruk", "krisis", "terjun"]
    scores = {
        "Fear": sum(1 for w in fear_words if w in text),
        "Greed": sum(1 for w in greed_words if w in text),
        "Hope": sum(1 for w in hope_words if w in text),
        "Panic": sum(1 for w in panic_words if w in text)
    }
    return max(scores, key=scores.get) if any(scores.values()) else "Neutral"

def analyze_sentiment_ai(text):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        client = google_genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f'Klasifikasikan sentiment berita keuangan Indonesia ini: Fear/Greed/Hope/Panic/Neutral. Jawab 1 kata saja.\n\nBerita: {text}'
        )
        result = response.text.strip()
        if result in ["Fear", "Greed", "Hope", "Panic", "Neutral"]:
            return result
        return "Neutral"
    except Exception as e:
        print(f"Gemini error: {e}")
        return analyze_sentiment(text)

def get_db_connection():
    retries = 5
    while retries > 0:
        try:
            return psycopg2.connect(**DB_CONFIG)
        except psycopg2.OperationalError:
            retries -= 1
            print(f"DB not ready, retrying... ({retries} left)")
            time.sleep(3)
    raise Exception("Could not connect to database")

def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            link TEXT,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# =========================
# 4. ROUTES
# =========================

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route("/")
def home():
    return "DevOps App Running 🚀"

@app.route("/fetch")
def fetch_rss():
    rss_sources = [
        "https://www.cnbcindonesia.com/rss",
        "https://ekonomi.bisnis.com/rss",
        "https://rss.kontan.co.id/market",
        "https://finance.detik.com/rss",
        "https://www.idxchannel.com/rss",
        "https://investor.id/rss",
        "https://katadata.co.id/rss",
        "https://www.republika.co.id/rss/ekonomi",
    ]

    conn = get_db_connection()
    cur = conn.cursor()
    total_saved = 0

    for url in rss_sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                sentiment = analyze_sentiment_ai(entry.title)
                cur.execute(
                    "INSERT INTO articles (title, link, sentiment) VALUES (%s, %s, %s)",
                    (entry.title, entry.link, sentiment)
                )
                total_saved += 1
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()

    return {"message": f"Saved {total_saved} articles from {len(rss_sources)} sources 🚀"}

@app.route("/data")
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, link, sentiment
        FROM articles
        ORDER BY id DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "title": row[0],
            "link": row[1],
            "sentiment": row[2]
        })
    return jsonify(result)

@app.route("/sentiment")
def get_sentiment():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT sentiment, COUNT(*) as total
        FROM articles
        WHERE sentiment IS NOT NULL
        GROUP BY sentiment
        ORDER BY total DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "sentiment": row[0],
            "total": row[1]
        })
    return jsonify(result)

@app.route("/notify")
def notify_telegram():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT sentiment, COUNT(*) as total
        FROM articles
        WHERE sentiment IS NOT NULL
        GROUP BY sentiment
        ORDER BY total DESC;
    """)
    rows = cur.fetchall()

    dominant = rows[0][0] if rows else "Neutral"
    
    # Keyword relevan pasar saham/investasi
    market_keywords = ['saham', 'ihsg', 'bursa', 'rupiah', 'emas', 'investasi', 
                        'pasar modal', 'reksadana', 'obligasi', 'bei', 'idx',
                        'cuan', 'profit', 'untung', 'rugi', 'ekonomi', 'inflasi',
                        'bank', 'kripto', 'crypto', 'bitcoin']

    cur.execute("""
        SELECT title FROM articles
        ORDER BY id DESC LIMIT 30;
    """)
    all_titles = [r[0] for r in cur.fetchall()]

    # Prioritaskan judul yang relevan
    relevant = [t for t in all_titles if any(k in t.lower() for k in market_keywords)]
    headlines = relevant[:3] if relevant else all_titles[:3]
    cur.close()
    conn.close()

    from datetime import datetime
    now = datetime.now().strftime("%d %b %Y")
    now_short = datetime.now().strftime("%d/%-m")
    total = sum(r[1] for r in rows)
    emoji = {"Fear": "🔴", "Greed": "🟢", "Hope": "🟡", "Panic": "⚫", "Neutral": "⚪"}
    dominant_emoji = emoji.get(dominant, "⚪")

    interpretasi = {
        "Fear": "Pasar sedang tertekan. Banyak aksi jual. Hati-hati.",
        "Greed": "Pasar sedang euforia. Waspadai FOMO.",
        "Hope": "Pasar menunggu katalis. Sentimen mulai membaik.",
        "Panic": "Pasar panik. Potensi oversold, perlu dicermati.",
        "Neutral": "Pasar konsolidasi. Belum ada arah yang jelas."
    }

    interpretasi_short = {
        "Fear": "Pasar tertekan, aksi jual dominan.",
        "Greed": "Euforia pasar, waspadai FOMO.",
        "Hope": "Sentimen membaik, tunggu katalis.",
        "Panic": "Pasar panik, potensi oversold.",
        "Neutral": "Konsolidasi, belum ada arah jelas."
    }

    # === PESAN 1: Format Telegram ===
    tg_lines = [
        f"📊 *Market Pulse Monitor*",
        f"🗓 {now}",
        f"",
        f"━━━━━━━━━━━━━━━",
        f"DOMINANT: {dominant_emoji} *{dominant.upper()}*",
        f"━━━━━━━━━━━━━━━",
        f"",
    ]
    for row in rows:
        e = emoji.get(row[0], "⚪")
        pct = round((row[1] / total) * 100)
        tg_lines.append(f"{e} {row[0]:<8}: {row[1]} berita ({pct}%)")
    tg_lines += [
        f"",
        f"📌 *Interpretasi:*",
        f"{interpretasi.get(dominant, '')}",
        f"",
        f"📰 *Headline Terkini:*",
    ]
    for h in headlines:
        tg_lines.append(f"• {h[:60]}...")
    tg_lines += ["", f"🔗 github.com/Rakamalik/market-pulse-monitor"]
    tg_message = "\n".join(tg_lines)

    # === PESAN 2: Format X/Twitter ===
    MAX = 280
    body = f"📊 Market Pulse Monitor — {now_short}\n\n"
    for row in rows:
        e = emoji.get(row[0], "⚪")
        pct = round((row[1] / total) * 100)
        body += f"{e} {row[0]}: {pct}%\n"
    body += f"\n{interpretasi_short.get(dominant, '')}\n"
    hashtags = "#IHSG #Saham"

    headline_lines = ""
    header = "\n📰 Headline:\n"
    for h in headlines:
        candidate = f"• {h[:45]}\n"
        test = body + (header if not headline_lines else "") + headline_lines + candidate + hashtags
        if len(test) <= MAX:
            if not headline_lines:
                headline_lines += header
            headline_lines += candidate

    tweet = body + headline_lines + "\n" + hashtags

    # === KIRIM KE TELEGRAM ===
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    tg_url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Kirim pesan 1
    requests.post(tg_url, json={
        "chat_id": chat_id,
        "text": tg_message,
        "parse_mode": "Markdown"
    })

    # Kirim pesan 2
    requests.post(tg_url, json={
        "chat_id": chat_id,
        "text": f"📤 *Draft X:*\n\n`{tweet}`",
        "parse_mode": "Markdown"
    })

    return {"message": "Notifications sent to Telegram ✅"}
	

@app.route("/ingest-ohlcv", methods=["POST"])
def ingest_ohlcv():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv (
            id SERIAL PRIMARY KEY,
            ticker TEXT,
            date DATE,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, date)
        );
    """)
    for row in data:
        cur.execute("""
            INSERT INTO ohlcv (ticker, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker, date) DO UPDATE SET
                close = EXCLUDED.close,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                volume = EXCLUDED.volume;
        """, (row['ticker'], row['date'], row['open'], row['high'], row['low'], row['close'], row['volume']))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": f"Saved {len(data)} rows"}
# =========================
# 5. RUN APP
# =========================
if __name__ == "__main__":
    create_table()
    app.run(host="0.0.0.0", port=5000)
