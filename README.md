# Real-Time Trade Settlement Risk Monitoring System

## Overview

A production-inspired real-time trade settlement monitoring platform that simulates financial trade processing, performs ML-based fraud detection and risk scoring, streams live events, stores them in PostgreSQL, and visualizes operational metrics through Grafana dashboards.

---

## Architecture

Producer
        ↓
Kafka
        ↓
Consumer
        ↓
PostgreSQL
        ↓
FastAPI
        ├── REST API
        ├── WebSocket
        ├── Prometheus Metrics
        ↓
Grafana Dashboard

---

## Features

- Real-time trade streaming
- Kafka event processing
- ML-based fraud prediction
- Risk scoring engine
- PostgreSQL storage
- FastAPI REST APIs
- WebSocket live updates
- Grafana dashboards
- Prometheus monitoring
- Dockerized microservices

---

## Tech Stack

Backend
- FastAPI
- Python
- SQLAlchemy

Streaming
- Apache Kafka

Database
- PostgreSQL

Monitoring
- Grafana
- Prometheus

Deployment
- Docker
- Docker Compose

Machine Learning
- Scikit-learn
- Pandas
- NumPy

---

## Project Structure

```
app/
dashboard/
producer.py
consumer.py
docker-compose.yml
requirements.txt
Dockerfile
Dockerfile.api
Dockerfile.dashboard
```

---

## Running Locally

```bash
docker compose up --build
```

---

## Dashboard

Grafana provides

- Trade volume
- Settlement status
- Broker risk
- Failed trades
- ML fraud detection
- Risk score trends
- High-risk trades

---

## Future Improvements

- Cloud deployment
- Kubernetes
- CI/CD pipeline
- JWT authentication
- Alert Manager
- Horizontal scaling

---

## Author

**Sarvasetty Revanth Kumar**