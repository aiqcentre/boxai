# BoxAI Project Documentation

## 📋 Project Overview

**BoxAI** is a comprehensive film analytics and box office prediction system that combines:
- **Film data analytics** via DuckDB database queries
- **Australian location information** via REST APIs
- **Box office revenue prediction** using machine learning models
- **Interactive chatbot interface** built with Streamlit and AI agents

---

## 🏗️ Current Architecture

### Core Components

#### 1. **Frontend Application**
- **`app.py`** (Main Streamlit Application)
  - Multi-agent chatbot interface
  - Integrates SQL queries, Australian location APIs, and ML predictions
  - Uses pydantic-ai for intelligent agent routing
  - Dynamically loads API endpoints from README.md
  - Provides safe, read-only database access

#### 2. **Machine Learning Models**

##### Week 1 Gross Prediction (Model 1)
- **`final_model.py`** - Training script for ExtraTreeRegressor
- **`boxoffice_preprocessor.py`** - Feature engineering and preprocessing
- **`OOP.py`** - BoxOfficeModel class for predictions
- **`boxoffice_model.pkl`** - Serialized trained model
- Predicts first week box office gross based on:
  - Censor rating
  - Distributor name
  - Release date
  - Concurrent films statistics
  - Theater/screen counts

##### Final Total Prediction (Model 2)
- **`final_total_predictor.py`** - XGBoost-based predictor class
- **`final_total/`** - Model artifacts directory
  - `model.booster.json` - XGBoost model
  - `metadata.json` - Model configuration
  - `schema.json` - Feature schema
  - `training_metrics.json` - Performance metrics
- Predicts final total gross from week 1 performance
- Single feature: `wk1_total` (log-transformed)

#### 3. **API Service**
- **`boxoffice_api.py`** - FastAPI application
  - `/predict1` - Week 1 gross prediction endpoint
  - `/predict2` - Final total prediction endpoint
  - `/` - Health check endpoint
  - Integrated with FastAPI-MCP
- **`Procfile`** - Deployment configuration for PaaS (Heroku/DigitalOcean)

#### 4. **Data Layer**
- **`data/numero.duckdb`** - DuckDB database with film records
  - Contains JSON-structured film data
  - Fields: title, distributor, ratings, gross, theater counts, etc.
- **`read_data.py`** - Utility for viewing/exploring database

#### 5. **Supporting Files**
- **`prompts.py`** - System prompts for SQL and answer agents
- **`style/styles.css`** - Custom CSS for Streamlit UI
- **`requirements.txt`** - Python dependencies
- **`README.md`** - Comprehensive documentation with API endpoints
- **`ways-of-working.md`** - Git workflow and branching strategy

#### 6. **Exploration & Development**
- **`model_1.ipynb`** - Model development notebook
- **`wrangle_visualize.ipynb`** - Data wrangling and visualization
- **`Data Exploration/`**
  - `Data Wrangling.ipynb` - Data preprocessing exploration
  - `XGB_Model.ipynb` - XGBoost model development
- **`model_1.html`** & **`wrangle_visualize.html`** - Exported notebook views

---

## 🔄 How Components Fit Together

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                         (app.py)                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Streamlit Chatbot with Multi-Agent System               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────┬─────────────────────┬────────────────────┬────────────────┘
     │                     │                    │
     ▼                     ▼                    ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  SQL Agent  │    │   AU Agent   │    │  Predict Agent  │
│ (prompts.py)│    │ (REST APIs)  │    │  (ML Models)    │
└──────┬──────┘    └──────────────┘    └────────┬────────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐                        ┌──────────────────┐
│   DuckDB    │                        │   FastAPI Server │
│ numero.duckdb│                        │ boxoffice_api.py │
└─────────────┘                        └────────┬─────────┘
                                               │
                                   ┌───────────┴───────────┐
                                   ▼                       ▼
                          ┌─────────────────┐    ┌────────────────┐
                          │  Model 1 (Week1)│    │ Model 2 (Final)│
                          │  OOP.py         │    │ final_total_   │
                          │  preprocessor   │    │ predictor.py   │
                          └─────────────────┘    └────────────────┘
```

### Data Flow

1. **User Query** → Streamlit chatbot (`app.py`)
2. **Query Classification** → Agent routing based on keywords
3. **Processing Paths:**
   
   **Path A: Film Analytics (SQL)**
   - SQL Agent generates DuckDB query
   - Executes against `numero.duckdb`
   - Answer Agent formats results
   
   **Path B: Australian Location Info**
   - AU Agent calls REST APIs
   - Returns city/state information
   
   **Path C: Box Office Predictions**
   - Predict Agent may query database for film details
   - Calls FastAPI endpoints (`/predict1`, `/predict2`)
   - Models return predictions (Week 1 or Final Total)

4. **Response Formatting** → Display in Streamlit tabs (Answer, SQL, Table, JSON)

---

## 📁 Current Directory Structure Issues

### Problems Identified

1. **Code Duplication**
   - Files exist in both root and `ML_prediction/` folder
   - Confusion about which version is canonical
   - Risk of inconsistencies

2. **Inconsistent Naming**
   - `OOP.py` - Not descriptive (should reflect BoxOfficeModel)
   - `final_model.py` vs `final_total_predictor.py` - Unclear distinction
   - `numero.duckdb` - Non-descriptive database name

3. **Mixed Concerns**
   - Training scripts mixed with deployment code
   - Notebooks scattered across root and subdirectories
   - HTML exports clutter root directory

4. **Unclear Module Boundaries**
   - `ML_prediction/` folder has redundant structure
   - No clear separation of concerns (data, models, api, frontend)

---

## 🎯 Recommended Directory Structure

```
boxai/
│
├── README.md
├── requirements.txt
├── .gitignore
├── project.md
├── ways-of-working.md
├── Procfile
│
├── src/                           # Source code
│   ├── __init__.py
│   │
│   ├── frontend/                  # Streamlit application
│   │   ├── __init__.py
│   │   ├── app.py                 # Main Streamlit app
│   │   ├── prompts.py             # Agent prompts
│   │   └── assets/
│   │       └── styles.css
│   │
│   ├── api/                       # FastAPI service
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI app (formerly boxoffice_api.py)
│   │   └── schemas.py             # Pydantic request/response models
│   │
│   ├── models/                    # ML models
│   │   ├── __init__.py
│   │   ├── week1_model.py         # Week 1 prediction model (formerly OOP.py)
│   │   ├── final_total_model.py   # Final total predictor
│   │   ├── preprocessor.py        # Feature engineering
│   │   └── artifacts/
│   │       ├── week1_model.pkl
│   │       └── final_total/
│   │           ├── model.booster.json
│   │           ├── metadata.json
│   │           ├── schema.json
│   │           └── training_metrics.json
│   │
│   ├── training/                  # Model training scripts
│   │   ├── __init__.py
│   │   ├── train_week1_model.py   # Train Week 1 model (formerly final_model.py)
│   │   └── train_final_total.py   # Train final total model
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── database.py            # Database utilities
│       └── data_explorer.py       # Data exploration tool (formerly read_data.py)
│
├── data/                          # Data storage
│   └── boxoffice.duckdb           # Main database (renamed from numero.duckdb)
│
├── notebooks/                     # Jupyter notebooks
│   ├── 01_data_wrangling.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   ├── 03_week1_model_development.ipynb
│   └── 04_final_total_xgboost.ipynb
│
├── docs/                          # Documentation
│   ├── api_documentation.md
│   ├── model_documentation.md
│   └── deployment_guide.md
│
└── tests/                         # Unit tests
    ├── __init__.py
    ├── test_preprocessor.py
    ├── test_models.py
    └── test_api.py
```

---

## 📝 Recommended File Renamings

| Current File | Recommended Name | Reason |
|--------------|------------------|--------|
| `OOP.py` | `src/models/week1_model.py` | More descriptive of functionality |
| `final_model.py` | `src/training/train_week1_model.py` | Clarifies it's a training script |
| `boxoffice_api.py` | `src/api/server.py` | Standard API naming convention |
| `boxoffice_preprocessor.py` | `src/models/preprocessor.py` | Shorter, clearer location |
| `final_total_predictor.py` | `src/models/final_total_model.py` | Consistent naming with week1 model |
| `read_data.py` | `src/utils/data_explorer.py` | More descriptive purpose |
| `prompts.py` | `src/frontend/prompts.py` | Group with related frontend code |
| `numero.duckdb` | `boxoffice.duckdb` | Self-documenting database name |
| `model_1.ipynb` | `notebooks/03_week1_model_development.ipynb` | Numbered, descriptive sequence |
| `wrangle_visualize.ipynb` | `notebooks/02_exploratory_analysis.ipynb` | Numbered, descriptive sequence |

---

## 🔧 Recommended Refactoring Steps

### Phase 1: Create New Structure (No Breaking Changes)
1. Create `src/` directory with subdirectories
2. Create `notebooks/` directory
3. Create `docs/` directory
4. Create `tests/` directory

### Phase 2: Move Files
1. Move frontend files to `src/frontend/`
2. Move API files to `src/api/`
3. Move model files to `src/models/`
4. Move training scripts to `src/training/`
5. Move utilities to `src/utils/`
6. Move notebooks to `notebooks/` with new names
7. Move model artifacts to `src/models/artifacts/`
8. Move styles to `src/frontend/assets/`
9. Rename database file

### Phase 3: Update Imports
1. Update all import statements to reflect new paths
2. Create `__init__.py` files for proper Python packages
3. Update `app.py` to import from `src.models`, `src.utils`, etc.
4. Update `server.py` (API) imports

### Phase 4: Clean Up
1. Remove duplicate files in `ML_prediction/`
2. Delete HTML export files (can regenerate if needed)
3. Update `.gitignore` to exclude `__pycache__`, `.ipynb_checkpoints`, etc.
4. Update documentation with new structure

### Phase 5: Configuration
1. Create `config.py` or `settings.py` for centralized configuration
2. Use environment variables for paths (DB_PATH, MODEL_PATH, etc.)
3. Update Procfile to reference new API location

---

## 🎨 Additional Improvements

### 1. **Add Configuration Management**
```python
# src/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "src" / "models" / "artifacts"

DB_PATH = DATA_DIR / "boxoffice.duckdb"
WEEK1_MODEL_PATH = MODEL_DIR / "week1_model.pkl"
FINAL_TOTAL_MODEL_PATH = MODEL_DIR / "final_total"

# API URLs from environment or defaults
AU_API_BASE = os.getenv("AU_API_BASE", "https://au-state-city-information-api.onrender.com")
PREDICT_API_BASE = os.getenv("PREDICT_API_BASE", "https://films-predict-app-wex9u.ondigitalocean.app")
```

### 2. **Add Module Init Files**
Create `__init__.py` in each package to expose key classes/functions:

```python
# src/models/__init__.py
from .week1_model import BoxOfficeWeek1Model
from .final_total_model import FinalTotalPredictor
from .preprocessor import BoxOfficePreprocessor

__all__ = ["BoxOfficeWeek1Model", "FinalTotalPredictor", "BoxOfficePreprocessor"]
```

### 3. **Separate API Schemas**
```python
# src/api/schemas.py
from pydantic import BaseModel, Field

class Week1PredictionRequest(BaseModel):
    censor_rating: str = Field(..., alias="censorRating")
    distributor_name: str = Field(..., alias="distributorName")
    week_date: str
    concurrent_films: list = []

class Week1PredictionResponse(BaseModel):
    predicted_gross: float

class FinalTotalRequest(BaseModel):
    wk1_total: float

class FinalTotalResponse(BaseModel):
    predicted_gross: float
```

### 4. **Add Logging**
```python
# src/utils/logger.py
import logging
import sys

def setup_logger(name: str, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

### 5. **Add Testing Structure**
```python
# tests/test_models.py
import pytest
from src.models import BoxOfficeWeek1Model, FinalTotalPredictor

def test_week1_prediction():
    # Test week 1 model predictions
    pass

def test_final_total_prediction():
    # Test final total predictions
    pass

# tests/test_api.py
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_predict1_endpoint():
    response = client.post("/predict1", json={
        "censorRating": "PG",
        "distributorName": "Disney",
        "week_date": "2024-06-15",
        "concurrent_films": []
    })
    assert response.status_code == 200
    assert "predicted_gross" in response.json()
```

---

## 📊 Summary of Benefits

### Current Issues
- ❌ Code duplication (root + ML_prediction folder)
- ❌ Unclear file purposes (OOP.py, final_model.py)
- ❌ Mixed training and deployment code
- ❌ No clear package structure
- ❌ Scattered notebooks
- ❌ No tests

### After Refactoring
- ✅ Clear separation of concerns
- ✅ Intuitive file naming
- ✅ Proper Python package structure
- ✅ Organized notebooks with sequence numbers
- ✅ Centralized configuration
- ✅ Test-ready structure
- ✅ Easy to navigate for new developers
- ✅ Scalable for future features

---

## 🚀 Migration Guide

### Quick Start for Refactoring

```powershell
# 1. Create new directory structure
New-Item -ItemType Directory -Path src/frontend, src/api, src/models/artifacts, src/training, src/utils, notebooks, docs, tests -Force

# 2. Move files (example commands)
Move-Item app.py src/frontend/
Move-Item prompts.py src/frontend/
Move-Item boxoffice_api.py src/api/server.py
Move-Item OOP.py src/models/week1_model.py
Move-Item boxoffice_preprocessor.py src/models/preprocessor.py
Move-Item final_total_predictor.py src/models/final_total_model.py
Move-Item final_model.py src/training/train_week1_model.py
Move-Item read_data.py src/utils/data_explorer.py
Move-Item style/styles.css src/frontend/assets/styles.css
Move-Item boxoffice_model.pkl src/models/artifacts/
Move-Item final_total src/models/artifacts/
Move-Item model_1.ipynb notebooks/03_week1_model_development.ipynb
Move-Item wrangle_visualize.ipynb notebooks/02_exploratory_analysis.ipynb
Move-Item "Data Exploration/Data Wrangling.ipynb" notebooks/01_data_wrangling.ipynb
Move-Item "Data Exploration/XGB_Model.ipynb" notebooks/04_final_total_xgboost.ipynb
Rename-Item data/numero.duckdb boxoffice.duckdb

# 3. Remove duplicates
Remove-Item -Recurse ML_prediction
Remove-Item model_1.html, wrangle_visualize.html
Remove-Item -Recurse "Data Exploration"

# 4. Create __init__.py files
New-Item src/__init__.py, src/frontend/__init__.py, src/api/__init__.py, src/models/__init__.py, src/training/__init__.py, src/utils/__init__.py, tests/__init__.py
```

---

## 🎯 Conclusion

The BoxAI project is a well-designed film analytics and prediction system with powerful ML capabilities. The recommended restructuring will:

1. **Improve Maintainability**: Clear separation of concerns
2. **Enhance Collaboration**: Easy for team members to navigate
3. **Enable Scaling**: Structure supports adding new features
4. **Facilitate Testing**: Clear test boundaries
5. **Better Documentation**: Organized notebooks and docs

This restructuring aligns with Python best practices and will make the project more professional and easier to work with for both current and future developers.
