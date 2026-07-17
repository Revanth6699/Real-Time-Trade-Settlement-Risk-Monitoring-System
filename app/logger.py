import logging

logging.getLogger("kafka").setLevel(logging.WARNING)
logging.getLogger("kafka.conn").setLevel(logging.WARNING)
logging.getLogger("kafka.cluster").setLevel(logging.WARNING)
logging.getLogger("kafka.coordinator").setLevel(logging.WARNING)
logging.getLogger("kafka.consumer").setLevel(logging.WARNING)
logging.getLogger("kafka.producer").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("trade-monitor")