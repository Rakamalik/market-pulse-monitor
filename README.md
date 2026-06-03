# Market Pulse Monitor

Real-time financial news tracker running on AWS EC2.

## Tech Stack
- **Flask** — REST API & RSS data collector
- **PostgreSQL** — Data storage
- **Docker & Docker Compose** — Containerization
- **GitHub Actions** — CI/CD pipeline
- **Prometheus & Grafana** — Monitoring
- **AWS EC2** — Cloud deployment

## Architecture
RSS Feed → Flask App → PostgreSQL → API Endpoints
↓
Docker Compose
↓
GitHub Actions (CI/CD)
↓
AWS EC2
↓
Prometheus + Grafana

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /fetch | GET | Fetch & store RSS articles |
| /data | GET | Retrieve stored articles |

## Features
- Automated RSS ingestion from financial news sources
- Persistent storage with PostgreSQL
- Containerized with Docker Compose
- Auto-deploy on every push via GitHub Actions
- System monitoring with Prometheus & Grafana

## Deployment
App is live on AWS EC2 with automated CI/CD pipeline.
Every push to master triggers automatic deployment.
