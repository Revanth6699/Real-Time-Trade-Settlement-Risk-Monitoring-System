import pandas as pd
import joblib

from sqlalchemy import create_engine

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import json
from datetime import datetime
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import os


# ----------------------------
# DATABASE
# ----------------------------

DATABASE_URL = (
    "postgresql://postgres:postgres@postgres:5432/trade_db"
)

engine = create_engine(DATABASE_URL)

# ----------------------------
# LOAD DATA
# ----------------------------

query = """
SELECT
    asset,
    broker,
    quantity,
    price,
    trade_amount,
    retry_count,
    risk_score
FROM trades
"""

df = pd.read_sql(query, engine)

print(f"\nLoaded {len(df)} trades")

# ----------------------------
# TARGET
# ----------------------------

df["target"] = (
    df["risk_score"] >= 70
).astype(int)

print("\nTarget Distribution:")
print(df["target"].value_counts())

# ----------------------------
# FEATURES
# ----------------------------

features = [
    "asset",
    "broker",
    "quantity",
    "price",
    "trade_amount",
    "retry_count"
]

X = df[features]

y = df["target"]

# ----------------------------
# SPLIT
# ----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# ----------------------------
# PREPROCESSING
# ----------------------------

categorical_features = [
    "asset",
    "broker"
]

numeric_features = [
    "quantity",
    "price",
    "trade_amount",
    "retry_count"
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "num",
            "passthrough",
            numeric_features
        )
    ]
)

# ----------------------------
# MODEL
# ----------------------------

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42,
    class_weight="balanced"
)

pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ----------------------------
# TRAIN
# ----------------------------

pipeline.fit(X_train, y_train)

# ----------------------------
# PREDICTIONS
# ----------------------------

preds = pipeline.predict(X_test)

# ----------------------------
# METRICS
# ----------------------------

accuracy = accuracy_score(y_test, preds)
precision = precision_score(y_test, preds)
recall = recall_score(y_test, preds)
f1 = f1_score(y_test, preds)

print("\nAccuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1:", f1)

print("\nClassification Report:")
print(classification_report(y_test, preds))

# ----------------------------
# SAVE METRICS
# ----------------------------

metrics = {
    "accuracy": float(accuracy),
    "precision": float(precision),
    "recall": float(recall),
    "f1_score": float(f1)
}

with open("app/ml/metrics.json", "w") as f:
    json.dump(metrics, f, indent=4)

print("\nMetrics saved to app/ml/metrics.json")

# ----------------------------
# SAVE MODEL
# ----------------------------

MODEL_PATH = "/app/app/models/high_risk_trade_model.pkl"

joblib.dump(pipeline, MODEL_PATH)

print(f"\nModel saved to {MODEL_PATH}")

# ----------------------------
# CONFUSION MATRIX
# ----------------------------

cm = confusion_matrix(y_test, preds)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Low Risk", "High Risk"]
)

disp.plot(cmap="Blues")

plt.title("Trade Settlement Risk Confusion Matrix")

confusion_matrix_file = (
    REPORTS_DIR /
    f"confusion_matrix_{timestamp}.png"
)

plt.savefig(
    confusion_matrix_file,
    bbox_inches="tight"
)

print(
    f"Confusion matrix saved to: "
    f"{confusion_matrix_file}"
)

plt.close()

# ----------------------------
# FEATURE IMPORTANCE
# ----------------------------

rf_model = pipeline.named_steps["model"]

feature_names = (
    pipeline.named_steps["preprocessor"]
    .get_feature_names_out()
)

importance = pd.DataFrame({
    "feature": feature_names,
    "importance": rf_model.feature_importances_
})

importance = importance.sort_values(
    by="importance",
    ascending=False
)

print("\nTop 15 Features")
print(importance.head(15))

plt.figure(figsize=(12, 6))

plt.barh(
    importance.head(15)["feature"],
    importance.head(15)["importance"]
)

plt.title("Top 15 Feature Importance")

plt.tight_layout()

feature_importance_file = (
    REPORTS_DIR /
    f"feature_importance_{timestamp}.png"
)

plt.savefig(
    feature_importance_file,
    bbox_inches="tight"
)

print(
    f"Feature importance saved to: "
    f"{feature_importance_file}"
)

plt.close()