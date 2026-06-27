import joblib
import pandas as pd

MODEL_PATH = "/app/app/models/high_risk_trade_model.pkl"

model = joblib.load(MODEL_PATH)

def predict_trade(trade_data):

    df = pd.DataFrame([{
        "asset": trade_data["asset"],
        "broker": trade_data["broker"],
        "quantity": trade_data["quantity"],
        "price": trade_data["price"],
        "trade_amount": trade_data["trade_amount"],
        "retry_count": trade_data.get("retry_count", 0)   
    }])

    prediction = int(model.predict(df)[0])

    probability = float(
        model.predict_proba(df)[0][1]
    )

    return prediction, probability