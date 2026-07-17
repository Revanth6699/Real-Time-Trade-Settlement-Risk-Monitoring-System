from kafka import KafkaConsumer
import json
import os
import random
import time

from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

KAFKA_SERVERS = os.getenv(
    "KAFKA_SERVERS",
    "localhost:9092"
)

print("KAFKA_SERVERS =", KAFKA_SERVERS)

# =========================================================
# KAFKA CONSUMER
# =========================================================

consumer = KafkaConsumer(
    "settlement-events",
    bootstrap_servers=KAFKA_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

# =========================================================
# SETTLEMENT STATUS CONFIG
# =========================================================

statuses = [
    "COMPLETED",
    "FAILED",
    "PENDING",
    "RETRYING"
]

weights = [70, 10, 15, 5]

# =========================================================
# CONSUMER LOOP
# =========================================================


for message in consumer:

    data = message.value

    # =========================================
    # SIMULATE SETTLEMENT STATUS
    # =========================================

    settlement_status = random.choices(
        statuses,
        weights=weights
    )[0]

    retry_count = 0

    if settlement_status == "RETRYING":
        retry_count = random.randint(1, 3)

    # =========================================
    # UPDATE EVENT
    # =========================================

    data["settlement_status"] = settlement_status
    data["retry_count"] = retry_count

    # =========================================
    # PRINT EVENT
    # =========================================

    print("\n===================================")
    print("Settlement Event Received")
    print("===================================")

    print(json.dumps(data, indent=4))

    # =========================================
    # DELAY
    # =========================================

    time.sleep(random.randint(1, 2))