# Film Box Office Gross Prediction API

This project provides a FastAPI-based web API for predicting film box office gross using machine learning models. It includes data preprocessing, model training, and prediction endpoints, along with Jupyter notebooks for data exploration and model development.

---

## Features

- **REST API** for predicting box office gross and final total gross
- **Data preprocessing** utilities
- **Trained ML models** and prediction logic
- **Jupyter notebooks** for data exploration, wrangling, and model development
- **Deployment-ready** with `Procfile` and `requirements.txt`

---

## Project Structure

```
.
├── boxoffice_api.py              # Main FastAPI app with API endpoints
├── boxoffice_preprocessor.py     # Data preprocessing logic
├── final_model.py                # Prediction model 1
├── final_total_predictor.py      # Prediction model 2
├── OOP.py                        # Object-oriented classes for model 1
├── model_1.ipynb                 # Model 1 development notebook
├── model_1.html                  # HTML export of model_1.ipynb
├── wrangle_visualize.ipynb       # Data wrangling & visualization notebook
├── wrangle_visualize.html        # HTML export of wrangle_visualize.ipynb
├── Data Exploration/             # Additional data exploration notebooks
│   ├── Data Wrangling.ipynb
│   └── XGB_Model.ipynb
├── data/
│   └── numero.duckdb             # DuckDB database file
├── final_total/
│   ├── metadata.json
│   ├── model.booster.json        # Trained model artifact for model 2
│   ├── schema.json
│   └── training_metrics.json
├── requirements.txt              # Python dependencies
├── Procfile                      # Deployment command for DigitalOcean
├── README.md                     # Project documentation
├── ways-of-working.md            # Collaboration guidelines
├── .gitignore
└── __pycache__/
```

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd boxai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the API Locally

```bash
uvicorn boxoffice_api:app --host 0.0.0.0 --port 8080
```

- The API will be available at [http://localhost:8080](http://localhost:8080)
- Interactive docs: [http://localhost:8080/docs](http://localhost:8080/docs)

---

## API Endpoints

- `GET /`  
  Health check endpoint.

- `POST /predict1`  
  Predicts box office gross for a film.  
  **Request body:**  
  ```json
  {
    "censorRating": "PG-13",
    "distributorName": "Universal",
    "week_date": "2025-10-08",
    "concurrent_films": []
  }
  ```

- `POST /predict2`  
  Predicts final total gross based on first week's gross.  
  **Request body:**  
  ```json
  {
    "wk1_total": 1000000
  }
  ```

---

## Data & Models

- **data/numero.duckdb**: Database file with raw or processed data.
- **final_total/**: Contains trained model artifacts and metadata for final total gross prediction.

---

## Notebooks

- **model_1.ipynb**: Model development and evaluation.
- **wrangle_visualize.ipynb**: Data wrangling and visualization.
- **Data Exploration/**: Additional notebooks for data analysis and modeling.

---

## Deployment

- The app is ready for deployment on DigitalOcean.
- The API will be available at [https://films-predict-app-wex9u.ondigitalocean.app/](https://films-predict-app-wex9u.ondigitalocean.app/)
- Interactive docs: [https://films-predict-app-wex9u.ondigitalocean.app/docs](https://films-predict-app-wex9u.ondigitalocean.app/docs)
---