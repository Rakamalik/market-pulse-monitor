# Market Pulse Monitor 2.0 📊

Real-time **Psychological Market Sentiment** tracker untuk pasar saham Indonesia.
Satu-satunya sistem yang menggabungkan analisis psikologis berbasis AI dengan **Psychological RRG (Relative Rotation Graph)** untuk emiten LQ45.

## What's New in 2.0
- 🧠 **AI Sentiment** via Gemini — bukan keyword matching
- 📈 **Psychological RRG Engine** — peta rotasi psikis trader
- 🤖 **Telegram Bot** — `/rrg BBCA BBRI` langsung kirim chart
- 📊 **LQ45 Coverage** — 53 emiten + IHSG + LQ45 Index

## Psychological RRG
Sistem ini memvisualisasikan **kondisi psikologis** emiten dalam 4 kuadran:

| Kuadran | Kondisi | Signal |
|---|---|---|
| LEADING (kanan atas) | Greed/FOMO | Ride the trend |
| WEAKENING (kanan bawah) | Fear/Profit Taking | Trailing stop |
| IMPROVING (kiri atas) | Hope/Akumulasi | Watchlist |
| LAGGING (kiri bawah) | Panic/Despair | No touch |

### Formula
Sumbu X (Logika Tren):
X = Z-Score(EMA(Close_emiten / Close_IHSG, 14)) × 10 + 100

Sumbu Y (Intensitas Emosi):
RVol = Volume / SMA(Volume, 20)
ATR_ROC = (ATR_t - ATR_t-5) / ATR_t-5
Y = Z-Score(RVol × ATR_ROC) × 10 + 100

## Architecture
LAPTOP (Windows)
push_ohlcv.py (daily 16:00)
↓
TENCENT CLOUD VM (101.32.169.164)
├── Flask App
│ ├── /health
│ ├── /fetch → RSS 8 sumber + Gemini AI
│ ├── /data → artikel + sentiment
│ ├── /sentiment → summary Fear/Greed/Hope/Panic
│ ├── /notify → kirim Telegram + draft X
│ ├── /ingest-ohlcv → terima OHLCV dari laptop
│ └── /rrg?tickers= → generate RRG chart PNG
├── PostgreSQL
│ ├── articles (sentiment)
│ └── ohlcv (53 tickers, LQ45)
├── Telegram Bot (polling)
│ ├── /rrg BBCA BBRI → RRG chart
│ ├── /sentiment → market summary
│ └── /fetch → ambil berita terbaru
├── Prometheus + Grafana (monitoring)
└── Docker Compose

## Tech Stack
- **Flask** — REST API
- **PostgreSQL** — Storage
- **Docker Compose** — Containerization
- **GitHub Actions** — CI/CD auto-deploy
- **Gemini AI** — Sentiment classification
- **Matplotlib** — RRG chart generation
- **Prometheus + Grafana** — Monitoring
- **Tencent Cloud** — Production server

## Telegram Bot Commands
| Command | Fungsi |
|---|---|
| `/rrg BBCA BBRI BMRI` | Generate Psychological RRG chart |
| `/sentiment` | Market sentiment summary hari ini |
| `/fetch` | Fetch berita terbaru |

## Data Pipeline
- OHLCV: yfinance via Windows laptop → push ke server daily
- News: 8 RSS sumber Indonesia (CNBC, Bisnis, Kontan, dll)
- AI: Gemini 2.5 Flash untuk klasifikasi sentiment

## Roadmap
- [x] AI sentiment via Gemini
- [x] Psychological RRG engine
- [x] Telegram bot with chart
- [x] LQ45 full coverage
- [ ] Web dashboard (Streamlit)
- [ ] Auto-post ke X/Twitter
- [ ] Sektor rotation view

## Contact
- GitHub: github.com/Rakamalik
- LinkedIn: linkedin.com/in/imam-raka-putra-2aa603339
