![Python](https://img.shields.io/badge/Python-3.10-blue)

![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green)

![Docker](https://img.shields.io/badge/Docker-Enabled-blue)

![License](https://img.shields.io/badge/License-MIT-green)


# Trade Settlement Risk Monitoring System

A real-time event-driven trade settlement monitoring platform that simulates financial trade processing, continuously evaluates settlement risk, detects anomalies, stores trades in PostgreSQL, exposes Prometheus metrics, and visualizes operational insights through Grafana.

---

## Overview

The project demonstrates how modern financial systems monitor trade settlements using an event-driven architecture.

Trades are continuously generated, processed, risk scored, persisted, monitored, and visualized in real time.

---

## Features

- Real-time trade generation
- Kafka-based event streaming (Redpanda)
- Settlement risk scoring
- Anomaly detection
- PostgreSQL (Neon) storage
- Redis caching
- Prometheus metrics
- Grafana dashboards
- Alertmanager notifications
- Telegram alerts
- Gmail alerts
- Dockerized deployment

---

## Project Structure

Real-Time-Trade-Settlement-Risk-Monitoring-System
│
├── app/
├── monitoring/
├── models/
├── screenshots/
│   ├── dashboard.png
│   ├── alerts.png
│   └── architecture.png
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md

## Tech Stack

| Category   | Technologies                      |
| ---------- | --------------------------------- |
| Backend    | Python, FastAPI, SQLAlchemy       |
| Streaming  | Redpanda                          |
| Database   | PostgreSQL (Neon)                 |
| Cache      | Redis (Upstash)                   |
| Monitoring | Prometheus, Grafana, Alertmanager |
| Deployment | Docker, Docker Compose, Render    |

---

## Architecture

```

Producer
   │
   ▼
Redpanda
   │
   ▼
Consumer
   │
   ▼
Risk Engine
   │
   ├────────► Redis
   │
   ▼
Neon PostgreSQL
   │
   ├────────► Prometheus
   │
   ▼
Grafana
   │
   ▼
Alertmanager
   │
   └── Telegram

```




## Rununing Locally



### Clone the repository

- git clone https://github.com/Revanth6699/Real-Time-Trade-Settlement-Risk-Monitoring-System.git

- cd Real-Time-Trade-Settlement-Risk-Monitoring-System

### Create environment variables

- cp .env.example .env
        {DATABASE_URL=
        REDIS_URL=
        KAFKA_BROKER=
        TELEGRAM_BOT_TOKEN=
        TELEGRAM_CHAT_ID=
        GMAIL_EMAIL=
        GMAIL_PASSWORD=}

### Run

- docker compose up --build



---


## Services

Service         Port
FastAPI	        8000
Grafana	        3000
Prometheus      9090
Alertmanager    9093

---

## Monitoring

Prometheus collects application metrics from FastAPI.

### Grafana Visualizes

- Trade throughput
- Risk score trend
- Market state
- Settlement status
- Broker exposure
- Asset distribution

### Alertmanager sends notifications

- Telegram


---

## Feature Improvements

- Authentication & RBAC
- Trade replay
- Historical analytics
- Kubernetes deployment
- Distributed consumer scaling