from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import sys
from src.models.preprocessor import BoxOfficePreprocessor
from src.models.week1_model import BoxOfficeModel
from src.models.final_total_model import FinalTotalPredictor
from fastapi_mcp import FastApiMCP

# Module alias for backward compatibility with pickled models
# The model was trained with the old module name 'boxoffice_preprocessor'
sys.modules['boxoffice_preprocessor'] = sys.modules['src.models.preprocessor']

app = FastAPI()
# Initialize FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount_http()

class Prediction1Request(BaseModel):
    """
    Request model for box office gross prediction.

    Attributes:
        censorRating (str): The censor rating of the film.
        distributorName (str): The name of the distributor.
        week_date (str): The release week date.
        concurrent_films (list): List of concurrent films with their features.
    """
    censorRating: str
    distributorName: str
    week_date: str
    concurrent_films: list = []

class Prediction1Response(BaseModel):
    """
    Response model for box office gross prediction.

    Attributes:
        predicted_gross (float): The predicted gross revenue.
    """
    predicted_gross: float


class BoxOfficeAPI:
    """
    BoxOfficeAPI class to handle predictions using the BoxOfficeModel.

    Methods:
        __init__: Initializes the BoxOfficeAPI with the model and preprocessor.
        predict: Predicts the box office gross for a given film.
    """
    def __init__(self):
        try:
            with open("src/models/artifacts/week1_model.pkl", "rb") as f:
                data = pickle.load(f)
            self.model = BoxOfficeModel(
                model=data["model"],
                preprocessor=data["preprocessor"],
                distributor_stats=data.get("distributor_stats", {})
            )
        except Exception as e:
            self.model = None
            print(f"Error loading model: {e}")

    def predict(self, request: Prediction1Request) -> Prediction1Response:
        """
        Predicts the box office gross for a given film.

        Args:
            request (Prediction1Request): The request containing film details.

        Returns:
            Prediction1Response: The predicted box office gross.
        """
        if self.model is None:
            raise HTTPException(status_code=500, detail="Model not loaded.")
        try:
            result = self.model.predict_from_json(request.model_dump())
            return Prediction1Response(predicted_gross=result)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

# --- FinalTotalPredictor integration ---
final_total_predictor = FinalTotalPredictor("src/models/artifacts/final_total")
final_total_predictor.load()

class Prediction2Request(BaseModel):
    """
    Request model for final total gross prediction.

    Attributes:
        wk1_total (float): The first week's total gross.
    """
    wk1_total: float

class Prediction2Response(BaseModel):
    """
    Response model for final total gross prediction.

    Attributes:
        predicted_final_total (float): The predicted final total gross.
    """
    predicted_gross: float

@app.post("/predict2", response_model=Prediction2Response)
def predict2_endpoint(request: Prediction2Request) -> Prediction2Response:
    """
    Endpoint to predict the final total gross based on the first week's gross.

    Args:
        request (Prediction2Request): The request containing the first week's gross.

    Returns:
        Prediction2Response: The predicted final total gross.
    """
    if request.wk1_total < 0:
        raise HTTPException(status_code=400, detail="wk1_total must be non-negative")
    result = final_total_predictor.predict_one({"wk1_total": request.wk1_total})
    return Prediction2Response(predicted_gross=result)

api = BoxOfficeAPI()

@app.post("/predict1", response_model=Prediction1Response)
def predict1_endpoint(request: Prediction1Request) -> Prediction1Response:
    """
    Endpoint to predict the box office gross for a film.

    Args:
        request (Prediction1Request): The request containing film details.

    Returns:
        Prediction1Response: The predicted box office gross.
    """
    return api.predict(request)

@app.get("/")
def root() -> dict:
    """
    Root endpoint to check if the API is running.

    Returns:
        dict: A message indicating the API is running.
    """
    return {"message": "BoxOfficeModel FastAPI is running."}
