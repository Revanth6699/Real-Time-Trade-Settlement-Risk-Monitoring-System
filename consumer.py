import json
import time

from kafka import KafkaConsumer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.trade import Trade
from app.database import Base

from app.redis_pubsub import publish_trade
import asyncio
from app.alerts import check_alerts, publish_alert

from app.ml.predict import predict_trade
from app.ml.risk_engine import calculate_risk


# =========================================================
# DATABASE CONFIG
# =========================================================

POSTGRES_SERVER = "postgres"
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"

# CONNECT TO DEFAULT POSTGRES DB FIRST
DEFAULT_DB_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:5432/postgres"
)

TARGET_DB = "trade_db"

# =========================================================
# CREATE DATABASE IF NOT EXISTS
# =========================================================

while True:
    try:
        default_engine = create_engine(DEFAULT_DB_URL)

        with default_engine.connect() as conn:
            conn.execute(text("commit"))

            result = conn.execute(
                text(
                    f"SELECT 1 FROM pg_database "
                    f"WHERE datname='{TARGET_DB}'"
                )
            )

            exists = result.scalar()

            if not exists:
                conn.execute(text(f"CREATE DATABASE {TARGET_DB}"))
                print(f"Database '{TARGET_DB}' created successfully")

            else:
                print(f"Database '{TARGET_DB}' already exists")

        break

    except Exception as e:
        print("Waiting for PostgreSQL...", e)
        time.sleep(5)

# =========================================================
# MAIN DATABASE CONNECTION
# =========================================================

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_SERVER}:5432/{TARGET_DB}"
)

while True:
    try:
        engine = create_engine(DATABASE_URL)

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        # CREATE TABLES
        Base.metadata.create_all(bind=engine)

        db = SessionLocal()

        print("Connected to trade_db successfully")
        break

    except Exception as e:
        print("Database connection failed:", e)
        time.sleep(5)

# =========================================================
# KAFKA CONNECTION
# =========================================================

while True:
    try:
        consumer = KafkaConsumer(
            "trades",
            bootstrap_servers="kafka:9092",
            value_deserializer=lambda m: json.loads(
                m.decode("utf-8")
            ),
            auto_offset_reset="latest",
            group_id="trade-group"
        )

        print("Kafka Consumer Started...")
        break

    except Exception as e:
        print("Kafka not ready... retrying", e)
        time.sleep(5)

# =========================================================
# CONSUMER LOOP
# =========================================================

for message in consumer:

    try:
        trade = message.value

        print("Received Trade:", trade)

        # =================================================
        # ML PREDICTION
        # =================================================

        prediction, probability = predict_trade(trade)

        # =================================================
        # RISK ENGINE
        # =================================================
        
        
        risk_score, anomaly_flag = calculate_risk(trade)
        risk_score = float(risk_score)


        # =================================================
        # INSERT TRADE
        # =================================================

        new_trade = Trade(
            trade_id=trade["trade_id"],
            asset=trade["asset"],
            broker=trade["broker"],
            quantity=trade["quantity"],
            price=trade["price"],
            trade_amount=trade["trade_amount"],
            settlement_status=trade["settlement_status"],
            retry_count=trade.get("retry_count", 0),

            risk_score=risk_score,
            anomaly_flag=anomaly_flag,

            ml_prediction=prediction,
            ml_probability=probability
        )
        db.add(new_trade)
        db.commit()


        trade_payload = {
            "trade_id": trade["trade_id"],
            "asset": trade["asset"],
            "broker": trade["broker"],
            "quantity": trade["quantity"],
            "price": trade["price"],
            "trade_amount": trade["trade_amount"],
            "risk_score": risk_score,
            "settlement_status": trade["settlement_status"],
            "anomaly_flag": anomaly_flag
        }

        alerts = check_alerts(trade_payload)

        if alerts:

            alert = {
                "trade_id": trade["trade_id"],
                "asset": trade["asset"],
                "broker": trade["broker"],
                "risk_score": risk_score,
                "alerts": alerts
            }

            asyncio.run(
                publish_alert(alert)
            )
        try:
            
            publish_trade(trade_payload)
            
            print(
                "Published to Redis:",
                trade["trade_id"]
            )

        except Exception as e:
            print(
                "Redis Publish Error:",
                e
            )
        print(
            "Trade inserted successfully:",
            trade["trade_id"]
        )
        
    except Exception as e:
        print("Insert failed:", e)
        db.rollback()