from app.utils.metrics_store import get_value
from prometheus_client import Gauge

TRADES_PRODUCED = Gauge(
    "trades_produced_total",
    "Produced Trades"
)

TRADES_STORED = Gauge(
    "trades_stored_total",
    "Stored Trades"
)

HIGH_RISK = Gauge(
    "high_risk_trades_total",
    "High Risk Trades"
)

ANOMALIES = Gauge(
    "anomalies_total",
    "Detected Anomalies"
)

TOTAL = Gauge(
    "total_trades_processed_total",
    "Processed Trades"
)

MARKET_STATE = Gauge(
    "market_state",
    "Market State"
)

ACTIVE_USERS = Gauge(
    "active_users",
    "Current Active Users"
)