"""
Stage 2: Financial Angle Finder
Ticker DIBATASI hanya dari universe 51 saham MPM.
"""

from google import genai
import os
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

TICKER_UNIVERSE = [
    "ACES.JK", "ADRO.JK", "AKRA.JK", "AMRT.JK", "ANTM.JK",
    "ASII.JK", "BBCA.JK", "BBNI.JK", "BBRI.JK", "BBTN.JK",
    "BMRI.JK", "BNGA.JK", "BRIS.JK", "BRPT.JK", "BSDE.JK",
    "BUKA.JK", "BYAN.JK", "CPIN.JK", "CTRA.JK", "EMTK.JK",
    "ESSA.JK", "EXCL.JK", "GOTO.JK", "HRUM.JK", "ICBP.JK",
    "INCO.JK", "INDF.JK", "INKP.JK", "INTP.JK", "ITMG.JK",
    "JSMR.JK", "KLBF.JK", "MAPI.JK", "MBMA.JK", "MDKA.JK",
    "MEDC.JK", "MIKA.JK", "MYOR.JK", "PGAS.JK", "PGEO.JK",
    "PTBA.JK", "PTPP.JK", "SIDO.JK", "SMGR.JK", "SRTG.JK",
    "TBIG.JK", "TKIM.JK", "TLKM.JK", "TPIA.JK", "UNTR.JK",
    "UNVR.JK", "WIKA.JK",
]

PROMPT_TEMPLATE = """Kamu adalah analis keuangan yang jago mencari celah/angle finansial dari topik viral non-finansial.

Ikuti KERANGKA 3 LANGKAH ini secara eksplisit untuk topik di bawah:
1. SIAPA pemain/pihak yang terlibat di topik ini?
2. APA dampak psikologis atau ekonomi dari topik ini ke konsumen/pasar?
3. SIAPA yang berpotensi UNTUNG atau RUGI secara finansial dari dampak tersebut?

Topik viral: {trend}
Konteks berita: {headline}

ATURAN PENTING - TICKER SAHAM:
Kamu HANYA BOLEH merekomendasikan ticker dari daftar berikut (jangan pernah menyebut ticker di luar daftar ini):
{ticker_list}

Jika TIDAK ADA satupun ticker dalam daftar di atas yang relevan dengan topik ini, set "topik_relevan": false dan kosongkan "kandidat".
Jangan memaksakan keterkaitan yang lemah hanya demi mengisi kandidat.

Jika ADA yang relevan, berikan maksimal 3 KANDIDAT angle finansial berbeda. Jawab HANYA dalam format JSON, tanpa markdown fence:

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
    ticker_list_str = ", ".join(TICKER_UNIVERSE)
    prompt = PROMPT_TEMPLATE.format(
        trend=trend,
        headline=headline or "(tidak ada headline)",
        ticker_list=ticker_list_str
    )

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
