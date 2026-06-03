
# =========================
# 1. IMPORT
# =========================
from flask import Flask, jsonify
import feedparser
import psycopg2

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


import time

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# =========================
# 4. ROUTES
# =========================

# Health check
@app.route("/health")
def health():
    return {"status": "ok"}

# Home
@app.route("/")
def home():
    return "DevOps App Running 🚀"

# Fetch RSS → save to DB
@app.route("/fetch")
def fetch_rss():
    url = "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
    feed = feedparser.parse(url)

    conn = get_db_connection()
    cur = conn.cursor()

    for entry in feed.entries[:5]:
        cur.execute(
            "INSERT INTO articles (title, link) VALUES (%s, %s)",
            (entry.title, entry.link)
        )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Data saved to database 🚀"}

# Get data from DB
@app.route("/data")
def get_data():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT title, link 
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
            "link": row[1]
        })

    return jsonify(result)

# =========================
# 5. RUN APP
# =========================
if __name__ == "__main__":
    create_table()  # auto create table
    app.run(host="0.0.0.0", port=5000)
