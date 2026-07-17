import json
import os
import time
import random

from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sqlalchemy.exc import IntegrityError, OperationalError

from app.database import SessionLocal
from app.models.trade import Trade

load_dotenv()

print("BOOTSTRAP =", os.getenv("KAFKA_BOOTSTRAP_SERVERS"))
print("TOPIC =", os.getenv("KAFKA_TOPIC"))
print("USER =", os.getenv("KAFKA_USERNAME"))
print("Connected to Neon PostgreSQL")


def calculate_risk(trade):
    risk = random.randint(10, 100)
    anomaly = risk >= 80
    return risk, anomaly


def create_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                os.getenv("KAFKA_TOPIC"),
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
                security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),
                sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
                sasl_plain_username=os.getenv("KAFKA_USERNAME"),
                sasl_plain_password=os.getenv("KAFKA_PASSWORD"),

                group_id="trade-monitor-group",

                auto_offset_reset="latest",
                enable_auto_commit=True,

                value_deserializer=lambda m: json.loads(m.decode("utf-8")),

                request_timeout_ms=60000,
                session_timeout_ms=30000,
                api_version_auto_timeout_ms=30000,
            )

            # Join the consumer group
            consumer.poll(timeout_ms=1000)

            # Skip any existing backlog ONLY on startup
            partitions = consumer.assignment()

            if partitions:
                consumer.seek_to_end(*partitions)

            print("Connected to Redpanda Cloud")
            print("Listening for NEW trades...\n")

            return consumer

        except Exception as e:
            print(f"Kafka connection failed: {e}")
            print("Retrying in 5 seconds...\n")
            time.sleep(5)


consumer = create_consumer()

while True:

    try:

        for message in consumer:

            data = message.value

            risk_score, anomaly_flag = calculate_risk(data)

            db = SessionLocal()

            try:

                trade = Trade(
                    trade_id=data["trade_id"],
                    asset=data["asset"],
                    broker=data["broker"],
                    quantity=data["quantity"],
                    price=data["price"],
                    trade_amount=data["trade_amount"],
                    settlement_status=data["settlement_status"],
                    risk_score=risk_score,
                    anomaly_flag=anomaly_flag,
                    timestamp=data["timestamp"],
                )

                db.add(trade)
                db.commit()

                print(
                    f"Stored: {trade.trade_id} | "
                    f"Risk={risk_score} | "
                    f"Anomaly={anomaly_flag}"
                )

            except IntegrityError:
                db.rollback()
                print(f"Duplicate skipped: {data['trade_id']}")

            except OperationalError:
                db.rollback()
                print("Neon connection lost. Reconnecting...")
                time.sleep(2)

            finally:
                db.close()

    except KafkaError as e:
        print(f"Kafka error: {e}")
        print("Reconnecting to Redpanda...\n")
        consumer = create_consumer()

    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Restarting consumer...\n")
        consumer = create_consumer()