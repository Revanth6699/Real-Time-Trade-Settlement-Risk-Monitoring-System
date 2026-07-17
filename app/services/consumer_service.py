import json
import os
import random
import time

from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from sqlalchemy.exc import IntegrityError, OperationalError

from app.logger import logger
from app.database import SessionLocal
from app.models.trade import Trade
from app.monitoring.prometheus_metrics import (
    TRADES_STORED,
    HIGH_RISK,
    ANOMALIES
)
from app.utils.metrics_store import increment



load_dotenv()


class ConsumerService:

    def __init__(self):
        self.consumer = None

    def calculate_risk(self):
        risk = random.randint(10, 100)
        return risk, risk >= 80

    def connect(self):

        while True:
            try:

                self.consumer = KafkaConsumer(

                    os.getenv("KAFKA_TOPIC"),

                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),

                    security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL"),

                    sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),

                    sasl_plain_username=os.getenv("KAFKA_USERNAME"),

                    sasl_plain_password=os.getenv("KAFKA_PASSWORD"),

                    group_id="trade-monitor-group",

                    auto_offset_reset="latest",

                    enable_auto_commit=False,

                    value_deserializer=lambda m: json.loads(
                        m.decode("utf-8")
                    ),

                    max_poll_records=25,

                    max_poll_interval_ms=600000,

                    session_timeout_ms=30000,

                    request_timeout_ms=60000,

                    api_version_auto_timeout_ms=30000,
                )

                logger.info("Consumer connected to Redpanda")
                return

            except Exception as e:

                logger.error(f"Consumer connection failed: {e}")
                time.sleep(5)

    def start(self):

        while True:

            try:

                self.connect()

                db = SessionLocal()

                try:

                    for message in self.consumer:

                        data = message.value

                        risk, anomaly = self.calculate_risk()

                        try:

                            logger.info(f"Received: {message.value['trade_id']}")

                            trade = Trade(

                                

                                trade_id=data["trade_id"],

                                asset=data["asset"],

                                broker=data["broker"],

                                quantity=data["quantity"],

                                price=data["price"],

                                trade_amount=data["trade_amount"],

                                settlement_status=data["settlement_status"],

                                risk_score=risk,

                                anomaly_flag=anomaly,

                                timestamp=data["timestamp"]

                            )

                            db.add(trade)
                            db.commit()

                            TRADES_STORED.inc()
                            
                            increment("trades_stored_total")
                            increment("total_trades_processed_total")

                            if risk >= 80:
                                HIGH_RISK.inc()
                                increment("high_risk_trades_total")

                            if anomaly:
                                ANOMALIES.inc()
                                increment("anomalies_total")  

                            self.consumer.commit()
                            logger.info("Trade committed")

                        except IntegrityError as e:
                            db.rollback()

                            logger.warning(
                                f"Duplicate trade skipped: {data['trade_id']}"
                            )

                            self.consumer.commit()
                            continue                      
                        except OperationalError:

                            logger.warning("Database connection lost. Reconnecting...")

                            db.rollback()
                            db.close()

                            db = SessionLocal()
                            

                        except Exception as e:

                            db.rollback()

                            logger.exception(f"Database error: {e}")

                finally:

                    db.close()

            except KafkaError as e:

                logger.error(f"Kafka error: {e}")

                time.sleep(5)

            except Exception as e:

                logger.exception(f"Consumer crashed: {e}")

                time.sleep(5)

if __name__ == "__main__":
    ConsumerService().start()