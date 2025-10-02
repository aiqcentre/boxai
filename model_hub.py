"""
Model Hub API (simple, with docs UI).

- Only one model for now: final_total (lives in experiments/final_total_baseline)
- Endpoints:
    - GET  /models: see what models are loaded and what they need
    - POST /predict/{model_name}: send JSON, get prediction
- Run with: uvicorn model_hub:app --reload
- Open docs UI: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

# Usual imports
import os, sys
from typing import Dict, Any, List
from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Make sure we can import stuff from src/ 
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from boxai.models.final_total_predictor import FinalTotalPredictor  # our model loader

# Where the model artifacts live
FINAL_TOTAL_DIR = os.path.join(REPO_ROOT, "experiments", "final_total_baseline")

# Enum for model names (lets FastAPI docs show a dropdown)
class ModelName(str, Enum):
    final_total = "final_total"

_registry: Dict[str, FinalTotalPredictor] = {}  # holds loaded models

# Helper to load a model and stash it in the registry
def _maybe_load(name: str, path: str) -> None:
    try:
        _registry[name] = FinalTotalPredictor(path)
    except Exception:
        pass  # don't crash if missing

# Load our only model at startup
_maybe_load(ModelName.final_total.value, FINAL_TOTAL_DIR)

# Pydantic schemas for request/response 
class PredictRequest(BaseModel):
    wk1_total: float = Field(..., ge=0, description="Week 1 total (non-negative)")

class PredictResponse(BaseModel):
    model: str
    prediction: float

class ModelInfo(BaseModel):
    name: str
    available: bool
    artifacts_dir: str
    features: List[str]

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

# Make the FastAPI app (sets up docs UI, tags, etc)
app = FastAPI(
    title="Model Hub",
    version="0.2.0",
    description="Unified endpoint to call multiple models. Use /models to list available model names, then POST /predict/{model_name} with JSON body.",
    openapi_tags=[
        {"name": "models", "description": "Model discovery"},
        {"name": "predict", "description": "Prediction endpoints"},
    ],
)

# Helper to list what features a model expects (for docs)
def _model_features(predictor: FinalTotalPredictor) -> List[str]:
    try:
        md = predictor.get_metadata()
        if "input_feature" in md:
            return [md["input_feature"]]
    except Exception:
        pass
    return ["wk1_total"]

# Endpoint: GET /models
# Shows what models are loaded, where their files are, and what inputs they need
@app.get("/models", response_model=ModelsResponse, tags=["models"], summary="List models")
def models() -> ModelsResponse:
    entries: List[ModelInfo] = []
    for name, path in [ (ModelName.final_total.value, FINAL_TOTAL_DIR) ]:
        predictor = _registry.get(name)
        available = predictor is not None
        features = _model_features(predictor) if predictor else []
        entries.append(ModelInfo(name=name, available=available, artifacts_dir=path, features=features))
    return ModelsResponse(models=entries)

# Endpoint: POST /predict/{model_name}
# Give it a model name and JSON with wk1_total, get a prediction back
@app.post("/predict/{model_name}", response_model=PredictResponse, tags=["predict"], summary="Predict using selected model")
def predict(model_name: ModelName, body: PredictRequest):
    name = model_name.value
    predictor = _registry.get(name)
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        pred = predictor.predict_one({"wk1_total": body.wk1_total})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"model": name, "prediction": pred}

# Run directly for local dev (python model_hub.py)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("model_hub:app", host="127.0.0.1", port=8000, reload=False)
