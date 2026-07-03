# Market Pulse Monitor 📊

Real-time financial market sentiment tracker for Indonesian market — deployed on AWS EC2.

Mengukur psikologi pasar keuangan Indonesia berdasarkan berita real-time, dengan distribusi otomatis ke Telegram.

## How It Works
8 RSS Sumber Berita Indonesia

↓

Flask App — fetch & analyze sentiment

↓

PostgreSQL — historical storage

↓

Sentiment Classification (Fear/Greed/Hope/Panic/Neutral)

↓

Telegram Bot — auto notification

↓

Ready-to-post content for X

## Sentiment Classification
| Label | Artinya |
|---|---|
| 🔴 Fear | Pasar takut, tekanan jual |
| 🟢 Greed | Pasar serakah, tekanan beli |
| 🟡 Hope | Pasar optimis, menunggu |
| ⚫ Panic | Pasar panik, aksi jual masif |
| ⚪ Neutral | Pasar netral |

## Tech Stack
- **Flask** — REST API & RSS data collector
- **PostgreSQL** — Historical data storage
- **Docker & Docker Compose** — Containerization
- **GitHub Actions** — CI/CD auto-deploy pipeline
- **Prometheus & Grafana** — System monitoring
- **AWS EC2** — Cloud production server
- **Telegram Bot API** — Automated content distribution

## RSS Sources
CNBC Indonesia, Bisnis.com, Kontan, Detik Finance, IDX Channel, Investor Daily, Katadata, Republika Ekonomi

## API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| /health | GET | System health check |
| /fetch | GET | Fetch & analyze latest news from 8 sources |
| /data | GET | Get articles with sentiment |
| /sentiment | GET | Sentiment summary report |
| /notify | GET | Send formatted sentiment report + X draft to Telegram |

## Features
- Bilingual sentiment analysis (Indonesian + English)
- Multi-source RSS ingestion with error handling
- Persistent PostgreSQL storage
- Docker Compose orchestration
- Auto-deploy on every GitHub push (CI/CD)
- Telegram bot for daily market sentiment summary
- Auto-generated, character-optimized content ready for X/Twitter
- Real-time monitoring with Prometheus & Grafana

## Sample Output (Telegram)
📊 Market Pulse Monitor

🗓 13 Jun 2026
━━━━━━━━━━━━━━━

DOMINANT: 🟢 GREED

━━━━━━━━━━━━━━━
🟢 Greed   : 8 berita (32%)

⚪ Neutral : 12 berita (48%)

🔴 Fear    : 5 berita (20%)
📌 Interpretasi:

Pasar sedang euforia. Waspadai FOMO.
📰 Headline Terkini:

Harga Emas Hari Ini Melonjak...

## Roadmap
- [x] Sentiment analysis (Fear/Greed/Hope/Panic/Neutral)
- [x] Multi-source RSS (8 sumber Indonesia)
- [x] Telegram bot integration
- [ ] Scheduled cron job for daily auto-notification
- [ ] Web dashboard for sentiment history
- [ ] LLM integration for deeper analysis

## Contact
- GitHub: github.com/Rakamalik
- LinkedIn: linkedin.com/in/imam-raka-putra-2aa603339
# Migrated to Tencent Cloud
# Migrated to Tencent Cloud
