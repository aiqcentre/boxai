

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import os
from typing import Any, Dict, List
from boxoffice_preprocessor import BoxOfficePreprocessor
from OOP import BoxOfficeModel
from final_total_predictor import FinalTotalPredictor


app = FastAPI()

# MCP naming 
MCP_MODEL_NAME = os.environ.get("MCP_MODEL_NAME", "boxoffice-model-1")
MCP_MODEL_VERSION = os.environ.get("MCP_MODEL_VERSION", "v1")
MCP_MODEL_DESCRIPTION = os.environ.get("MCP_MODEL_DESCRIPTION", "BoxOffice FastAPI MCP wrapper")

class PredictionRequest(BaseModel):
    censorRating: str
    distributorName: str
    week_date: str
    concurrent_films: list = []

class PredictionResponse(BaseModel):
    predicted_gross: float


class BoxOfficeAPI:
    def __init__(self):
        try:
            with open("boxoffice_model.pkl", "rb") as f:
                data = pickle.load(f)
            self.model = BoxOfficeModel(
                model=data["model"],
                preprocessor=data["preprocessor"],
                distributor_stats=data.get("distributor_stats", {})
            )
        except Exception as e:
            self.model = None
            print(f"Error loading model: {e}")

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        if self.model is None:
            raise HTTPException(status_code=500, detail="Model not loaded.")
        try:
            result = self.model.predict_from_json(request.model_dump())
            return PredictionResponse(predicted_gross=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


# MCP for batch predictions
class MCPPredictRequest(BaseModel):
    instances: List[Dict[str, Any]]


class MCPPredictResponse(BaseModel):
    predictions: List[float]

# --- FinalTotalPredictor integration ---
final_total_predictor = FinalTotalPredictor("final_total")
final_total_predictor.load()

class FinalTotalPredictRequest(BaseModel):
    wk1_total: float

class FinalTotalPredictResponse(BaseModel):
    predicted_final_total: float

@app.post("/final_total_predict", response_model=FinalTotalPredictResponse)
def final_total_predict_endpoint(request: FinalTotalPredictRequest) -> FinalTotalPredictResponse:
    if request.wk1_total < 0:
        raise HTTPException(status_code=400, detail="wk1_total must be non-negative")
    result = final_total_predictor.predict_one({"wk1_total": request.wk1_total})
    return FinalTotalPredictResponse(predicted_final_total=result)

api = BoxOfficeAPI()

@app.post("/predict1", response_model=PredictionResponse)
def predict_endpoint(request: PredictionRequest) -> PredictionResponse:
    return api.predict(request)

@app.get("/")
def root() -> dict:
    return {"message": "BoxOfficeModel FastAPI is running."}


@app.get("/mcp/metadata")
def mcp_metadata() -> dict:
    """Return simple MCP-style metadata so chatbots can discover this model."""
    health = "ready" if api.model is not None else "error: model not loaded"
    return {
        "id": MCP_MODEL_NAME,
        "name": MCP_MODEL_NAME,
        "version": MCP_MODEL_VERSION,
        "description": MCP_MODEL_DESCRIPTION,
        "endpoints": {
            "predict": "/mcp/predict",
            "health": "/",
            "raw_predict": "/predict1",
            "final_total_predict": "/final_total_predict",
        },
        "inputs": {"type": "table", "columns": "see /predict1 payload"},
        "outputs": {"type": "array", "items": "predicted_gross (float)"},
        "health": health,
    }


@app.post("/mcp/predict", response_model=MCPPredictResponse)
def mcp_predict(request: MCPPredictRequest) -> MCPPredictResponse:
    """Accepts {"instances": [{...}, ...]} and returns predictions array.
    Each instance should contain the fields expected by /predict1 (censorRating, distributorName, week_date, concurrent_films).
    """
    if not request.instances:
        raise HTTPException(status_code=400, detail="no instances provided")

    preds: List[float] = []
    for inst in request.instances:
        try:
            # Parse instance into the PredictionRequest Pydantic model to validate fields
            pr = PredictionRequest.parse_obj(inst)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"invalid instance format: {e}")

        resp = api.predict(pr)
        preds.append(resp.predicted_gross)

    return MCPPredictResponse(predictions=preds)
