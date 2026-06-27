import os
import json
from dotenv import load_dotenv
from kafka import KafkaProducer

load_dotenv()

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

print("KAFKA_SERVERS =", KAFKA_SERVERS)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
def send_settlement_event(data):

    producer.send(
        "settlement-events",
        value=data
    )

    producer.flush()