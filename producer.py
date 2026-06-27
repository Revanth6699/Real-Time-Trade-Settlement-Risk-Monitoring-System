import json
import uuid
import time
import random
from kafka import KafkaProducer
from kafka.errors import KafkaConnectionError

# Retry Kafka connection
producer = None

while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Connected to Kafka Producer")
    except Exception as e:
        print(f"Kafka not ready: {e}")
        time.sleep(5)
assets = ["AAPL", "TSLA", "MSFT", "AMZN"]
brokers = ["Goldman", "JP Morgan", "Citadel"]

print("Kafka Producer Started...")

while True:

    trade = {
        "trade_id": str(uuid.uuid4()),
        "asset": random.choice(assets),
        "broker": random.choice(brokers),
        "quantity": random.randint(1, 1000),
        "price": round(random.uniform(100, 1000), 2),
    }

    trade["trade_amount"] = round(
        trade["quantity"] * trade["price"], 2
    )

    trade["settlement_status"] = random.choices(
        ["PENDING", "FAILED", "COMPLETED"],
        weights=[50, 30, 20]
    )[0]
    
    producer.send("trades", value=trade)

    print(f"Trade Sent: {trade}")

    time.sleep(2)