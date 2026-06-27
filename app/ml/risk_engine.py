import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

risk_model = joblib.load(
    os.path.join(BASE_DIR, "risk_model.pkl")
)

anomaly_model = joblib.load(
    os.path.join(BASE_DIR, "anomaly_model.pkl")
)
# Broker institutional risk mapping
broker_risk_map = {
    "JP Morgan": 5,
    "Goldman": 10,
    "MorganStanley": 15,
    "Citadel": 20
}


def calculate_risk(trade):

    features = pd.DataFrame([{

        "trade_amount":
            trade["trade_amount"],

        "settlement_delay":
            trade.get("retry_count", 0),

        "broker_risk":
            broker_risk_map.get(
                trade["broker"],
                5
            ),

        "trade_frequency":
            trade["quantity"]

    }])

    # Predict risk score
    risk_score = risk_model.predict(features)[0]

    # Detect anomaly
    anomaly_prediction = anomaly_model.predict(features)[0]

    anomaly_flag = (
        True if anomaly_prediction == -1
        else False
    )

    return risk_score, anomaly_flag

