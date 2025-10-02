"""

Run:
    uvicorn multi_api:app --reload

Endpoints:
    GET /healthz          - basic health + model status
    GET /predict?wk1_total=1234  - returns prediction

Environment Variables:
    FINAL_TOTAL_ARTIFACTS  (optional) override artifacts directory
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query

# --- Path setup to import predictor from src/ ---
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from boxai.models.final_total_predictor import FinalTotalPredictor  # noqa: E402

# Resolve artifacts directory (env override or default)
ARTIFACTS_DIR = os.getenv(
    "FINAL_TOTAL_ARTIFACTS",
    os.path.join(REPO_ROOT, "experiments", "final_total_baseline")
)

# Instantiate predictor once (fail fast if artifacts missing)
try:
    predictor = FinalTotalPredictor(ARTIFACTS_DIR)
    MODEL_READY = True
    MODEL_ERROR: str | None = None
except Exception as e:  # broad intentionally for surface visibility
    predictor = None  # type: ignore
    MODEL_READY = False
    MODEL_ERROR = str(e)

app = FastAPI(title="Final Total Model API", version="1.0.0")


@app.get("/healthz")
def health() -> Dict[str, Any]:
    return {
        "status": "ok" if MODEL_READY else "error",
        "model_ready": MODEL_READY,
        "artifacts_dir": ARTIFACTS_DIR,
        "error": MODEL_ERROR,
    }


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "final-total",
        "endpoints": ["/healthz", "/predict"],
        "query_param": "wk1_total",
    }


@app.get("/predict")
def predict(wk1_total: float = Query(..., ge=0, description="Week 1 total (non-negative)")) -> Dict[str, Any]:
    if not MODEL_READY or predictor is None:
        raise HTTPException(status_code=503, detail=f"Model not ready: {MODEL_ERROR}")
    try:
        pred = predictor.predict_one({"wk1_total": wk1_total})
    except Exception as e:  # minimal surface
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "input": wk1_total,
        "prediction": pred,
        "model": "final_total",
    }

