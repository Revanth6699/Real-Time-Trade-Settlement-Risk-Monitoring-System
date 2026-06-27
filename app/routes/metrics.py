from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter()

@router.get("/model-metrics")
def get_model_metrics():

    metrics_file = Path("app/ml/metrics.json")

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    return metrics