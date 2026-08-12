"""
Stage 3+4: Validate & Enrich + Notify
"""

import os
import psycopg2
import pandas as pd
import requests
import json
from datetime import datetime

DB_CONFIG = {
    "host": "172.18.0.2",
    "database": "devopsdb",
    "user": "devops",
    "password": "password",
    "port": 5432
}


def get_ticker_performance(ticker_raw):
    ticker = ticker_raw.strip().upper()
    if not ticker.endswith('.JK') and not ticker.startswith('^'):
        ticker = ticker + '.JK'

    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT date, close, volume FROM ohlcv WHERE ticker=%s ORDER BY date DESC LIMIT 10",
        conn, params=(ticker,)
    )
    conn.close()

    if df.empty:
        return {
            'ticker': ticker,
            'verified': False,
            'reason': 'Ticker tidak ditemukan di database - cek manual apakah listed di IDX'
        }

    df = df.sort_values('date')
    latest_close = df['close'].iloc[-1]
    week_ago_close = df['close'].iloc[0]
    pct_change = ((latest_close - week_ago_close) / week_ago_close) * 100
    latest_date = df['date'].iloc[-1]

    return {
        'ticker': ticker,
        'verified': True,
        'latest_close': float(latest_close),
        'latest_date': str(latest_date),
        'pct_change_7d': round(float(pct_change), 2),
        'data_points': len(df)
    }


def extract_tickers_from_candidate(kandidat_text):
    import re
    pattern = r'\b[A-Z]{3,5}\.JK\b'
    found = re.findall(pattern, kandidat_text.upper())
    return list(set(found)) if found else []


def enrich_analysis(stage2_results):
    drafts = []

    for item in stage2_results:
        analysis = item.get('analysis', {})
        if not analysis.get('topik_relevan'):
            continue

        for kandidat in analysis.get('kandidat', []):
            ticker_text = kandidat.get('ticker_kandidat', '')
            tickers_found = extract_tickers_from_candidate(ticker_text)

            if not tickers_found:
                continue

            validated = [get_ticker_performance(t) for t in tickers_found]

            draft = {
                'topik': item['trend'],
                'headline_sumber': item.get('headline'),
                'angle': {
                    'siapa_terlibat': kandidat.get('siapa_terlibat'),
                    'dampak_ekonomi': kandidat.get('dampak_ekonomi'),
                    'potensi_untung_rugi': kandidat.get('potensi_untung_rugi'),
                },
                'ticker_validasi': validated,
                'alasan_ai': kandidat.get('alasan_singkat'),
                'generated_at': datetime.now().isoformat()
            }
            drafts.append(draft)

    return drafts


def print_draft_summary(drafts):
    print(f"\n=== {len(drafts)} Draft Siap Review ===\n")
    for i, d in enumerate(drafts, 1):
        print(f"[{i}] Topik: {d['topik']}")
        for tv in d['ticker_validasi']:
            if tv['verified']:
                arrow = "UP" if tv['pct_change_7d'] > 0 else "DOWN"
                print(f"    {tv['ticker']}: Rp{tv['latest_close']:,.0f} ({tv['pct_change_7d']:+.2f}% 7d) [{arrow}] - data per {tv['latest_date']}")
            else:
                print(f"    {tv['ticker']}: TIDAK TERVERIFIKASI - {tv['reason']}")
        print(f"    Angle: {d['alasan_ai'][:100]}...")
        print()


def send_telegram_notification(drafts):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("TELEGRAM_TOKEN/TELEGRAM_CHAT_ID tidak ditemukan, skip notifikasi")
        return

    if not drafts:
        message = "Content Agent: tidak ada draft relevan hari ini."
    else:
        lines = [
            "Content Agent - Draft Harian Siap",
            f"({len(drafts)} draft, cek drafts_output.json untuk detail lengkap)",
            "",
        ]
        for i, d in enumerate(drafts, 1):
            lines.append(f"[{i}] {d['topik']}")
            for tv in d['ticker_validasi']:
                if tv['verified']:
                    arrow = "naik" if tv['pct_change_7d'] > 0 else "turun"
                    lines.append(f"  {tv['ticker']}: Rp{tv['latest_close']:,.0f} ({tv['pct_change_7d']:+.2f}% 7d, {arrow})")
                else:
                    lines.append(f"  {tv['ticker']}: belum terverifikasi")
            lines.append(f"  {d['alasan_ai']}")
            lines.append("")
        message = "\n".join(lines)

        if len(message) > 4000:
            message = message[:3900] + "\n\n...(dipotong, cek drafts_output.json untuk lengkap)"

    tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(tg_url, json={
            "chat_id": chat_id,
            "text": message
        })
        if resp.status_code == 200:
            print("Notifikasi Telegram terkirim")
        else:
            print(f"Telegram API error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Gagal kirim notifikasi Telegram: {e}")


if __name__ == "__main__":
    from trend_finder import discover_trends
    from financial_angle_finder import process_topics

    topics = discover_trends(limit=10)
    stage2_results = process_topics(topics, max_topics=5)
    drafts = enrich_analysis(stage2_results)
    print_draft_summary(drafts)

    with open('drafts_output.json', 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)
    print("\nDraft lengkap disimpan ke drafts_output.json")

    send_telegram_notification(drafts)
