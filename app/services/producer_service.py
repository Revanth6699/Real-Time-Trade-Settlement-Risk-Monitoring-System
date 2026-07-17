import json
import uuid
import time
import random
import os

from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.logger import logger
from app.services.market_state import MarketState
from app.monitoring.prometheus_metrics import TRADES_PRODUCED, MARKET_STATE
from app.utils.metrics_store import increment, set_value



load_dotenv()

MARKET_VALUES = {
    "LOW": 0,
    "NORMAL": 1,
    "BUSY": 2,
    "PEAK": 3,
}


class ProducerService:

    def __init__(self):
        self.producer = None

        self.assets = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "TSLA",
            "AMZN",
            "NVDA"
        ]

        self.brokers = [
            "JP Morgan",
            "Goldman Sachs",
            "Morgan Stanley",
            "Barclays",
            "Citibank"
        ]

    def connect(self):

        while True:

            try:

                self.producer = KafkaProducer(
                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
                    security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),
                    sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
                    sasl_plain_username=os.getenv("KAFKA_USERNAME"),
                    sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    retries=5,
                    api_version_auto_timeout_ms=30000
                )

                logger.info("Producer connected to Redpanda")

                return

            except Exception as e:

                print(f"Producer connection failed: {e}")

                time.sleep(5)

    def start(self):

        

        self.connect()

        current_state = MarketState.get_state()

        MARKET_STATE.set(MARKET_VALUES[current_state])
        set_value(
            "market_state",
            MARKET_VALUES[current_state]
        )
        
        last_state_change = time.time()

        logger.info(f"Market State -> {current_state}")

        trade_count = 0

        while True:

            try:

                # Change market state every 60 seconds
                if time.time() - last_state_change >= 60:

                    current_state = MarketState.get_state()

                    MARKET_STATE.set(
                        MARKET_VALUES[current_state]
                    )

                    set_value(
                        "market_state",
                        MARKET_VALUES[current_state]
                    )


                    last_state_change = time.time()

                    logger.info(f"Market State -> {current_state}")

                trade = {
                    "trade_id": str(uuid.uuid4()),
                    "asset": random.choice(self.assets),
                    "broker": random.choice(self.brokers),
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

                self.producer.send(
                    os.getenv("KAFKA_TOPIC"),
                    trade
                )

                trade_count += 1
                TRADES_PRODUCED.inc()

                try:
                    increment("trades_produced_total")
                except Exception as e:
                    logger.warning(f"Metrics update failed: {e}")



                # Flush every 10 trades instead of every trade
                if trade_count % 10 == 0:
                    self.producer.flush()

                # Log every 100 trades
                if trade_count % 100 == 0:
                    logger.info(
                        f"Produced {trade_count} trades | Market={current_state}"
                    )

                delay = MarketState.get_delay(current_state)

                time.sleep(delay)

            except KafkaError as e:

                logger.error(f"Producer Error: {e}")

                self.connect()

            except Exception as e:

                logger.exception(e)

                time.sleep(5)

                self.connect()

if __name__ == "__main__":
    ProducerService().start()