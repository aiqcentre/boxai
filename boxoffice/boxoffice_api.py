

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
from boxoffice_preprocessor import BoxOfficePreprocessor
from OOP import BoxOfficeModel
from final_total_predictor import FinalTotalPredictor


app = FastAPI()

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
