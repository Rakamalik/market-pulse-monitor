"""
Stage 2: Financial Angle Finder
Dari topik viral (Stage 1), AI usulkan 3 kandidat angle keuangan
menggunakan kerangka 3-langkah.
"""

from google import genai
import os
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

PROMPT_TEMPLATE = """Kamu adalah analis keuangan yang jago mencari celah/angle finansial dari topik viral non-finansial.

Ikuti KERANGKA 3 LANGKAH ini secara eksplisit untuk topik di bawah:
1. SIAPA pemain/pihak yang terlibat di topik ini? (perusahaan, sektor, individu berpengaruh, institusi)
2. APA dampak psikologis atau ekonomi dari topik ini ke konsumen/pasar? (sentimen, kepercayaan, perilaku belanja, kebijakan)
3. SIAPA yang berpotensi UNTUNG atau RUGI secara finansial dari dampak tersebut? (termasuk kandidat ticker saham Indonesia (.JK) jika relevan)

Topik viral: {trend}
Konteks berita: {headline}

Berikan 3 KANDIDAT angle finansial berbeda (bukan cuma satu). Untuk tiap kandidat, jawab persis mengikuti kerangka 3 langkah di atas secara singkat, lalu simpulkan dengan kandidat ticker saham (jika ada) dan alasan singkat.

PENTING:
- Kalau topik ini TIDAK punya celah keuangan yang masuk akal, katakan terus terang "tidak relevan" - jangan dipaksakan.
- Jangan mengarang data. Kalau tidak yakin soal ticker/perusahaan, katakan "perlu verifikasi lebih lanjut".
- Jawab HANYA dalam format JSON, tanpa markdown fence, dengan struktur:

{{
  "topik_relevan": true/false,
  "kandidat": [
    {{
      "siapa_terlibat": "...",
      "dampak_ekonomi": "...",
      "potensi_untung_rugi": "...",
      "ticker_kandidat": "...",
      "alasan_singkat": "..."
    }}
  ]
}}
"""


def find_financial_angle(trend, headline=""):
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY tidak ditemukan di environment"}

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = PROMPT_TEMPLATE.format(trend=trend, headline=headline or "(tidak ada headline)")

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )
        text = response.text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        parsed = json.loads(text)
        return parsed

    except json.JSONDecodeError:
        return {"error": "Gagal parse JSON dari response AI", "raw_response": text}
    except Exception as e:
        return {"error": str(e)}


def process_topics(topics, max_topics=5):
    results = []
    for t in topics[:max_topics]:
        print(f"\n=== Menganalisis: {t['trend']} ===")
        angle = find_financial_angle(t['trend'], t.get('headline', ''))
        results.append({
            'trend': t['trend'],
            'traffic': t.get('traffic'),
            'headline': t.get('headline'),
            'analysis': angle
        })

        if angle.get('topik_relevan'):
            print(f"  RELEVAN - {len(angle.get('kandidat', []))} kandidat ditemukan")
            for i, k in enumerate(angle.get('kandidat', []), 1):
                print(f"  [{i}] Ticker: {k.get('ticker_kandidat')} - {k.get('alasan_singkat')}")
        elif 'error' in angle:
            print(f"  ERROR: {angle['error']}")
        else:
            print("  Tidak relevan secara finansial")

    return results


if __name__ == "__main__":
    from trend_finder import discover_trends
    topics = discover_trends(limit=10)
    results = process_topics(topics, max_topics=5)

    print("\n\n=== RINGKASAN LENGKAP ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))
