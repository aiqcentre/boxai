"""

Run:
    uvicorn api_min:app --reload --port 8000

Test:
    curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"wk1_total":1234}'


"""
from __future__ import annotations
import os, sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Ensure src/ is importable when running from repo root
repo_root = os.path.abspath(os.path.dirname(__file__))
src_path = os.path.join(repo_root, 'src')
if src_path not in sys.path:
    sys.path.append(src_path)

from boxai.models.final_total_predictor import FinalTotalPredictor  # type: ignore  # noqa: E402

ARTIFACTS_DIR = os.getenv("FINAL_TOTAL_ARTIFACTS", "experiments/final_total_baseline")

# Instantiate once (simple; restart process if artifacts change)
predictor = FinalTotalPredictor(ARTIFACTS_DIR)

app = FastAPI(title="Final Total Predictor", version="0.1.1")


class PredictRequest(BaseModel):
    wk1_total: float = Field(..., ge=0, description="Week 1 total value (non-negative)")


@app.post("/predict")
def predict(payload: PredictRequest):
    if payload.wk1_total < 0:
        raise HTTPException(status_code=400, detail="wk1_total must be non-negative")
    pred = predictor.predict_one({"wk1_total": payload.wk1_total})
    return {"prediction": pred}
