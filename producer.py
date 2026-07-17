import json
import uuid
import time
import random
import os

from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
TOPIC = os.getenv("KAFKA_TOPIC")

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),
    sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
    sasl_plain_username=os.getenv("KAFKA_USERNAME"),
    sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    api_version_auto_timeout_ms=30000,
)

print("Connected to Redpanda Cloud")

assets = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "TSLA",
    "AMZN",
    "NVDA"
]

brokers = [
    "JP Morgan",
    "Goldman Sachs",
    "Morgan Stanley",
    "Barclays",
    "Citibank"
]

while True:

    trade = {
        "trade_id": str(uuid.uuid4()),
        "asset": random.choice(assets),
        "broker": random.choice(brokers),
        "quantity": random.randint(1, 1000),
        "price": round(random.uniform(100, 1000), 2),
        "settlement_status": random.choice(
            ["SUCCESS", "FAILED", "PENDING"]
        ),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    trade["trade_amount"] = round(
        trade["quantity"] * trade["price"],
        2
    )

    try:
        producer.send(TOPIC, trade)
        producer.flush()
        print("Produced:", trade)

    except KafkaError as e:
        print(e)

    time.sleep(2)