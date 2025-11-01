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

---

## 🧪 Smoke Testing Plan

After reorganizing the project structure, follow this comprehensive testing plan to verify everything still works correctly.

### Pre-Test Checklist

#### 1. Verify File Structure
```powershell
# Check all critical files exist in new locations
Test-Path src/frontend/app.py
Test-Path src/api/server.py
Test-Path src/models/week1_model.py
Test-Path src/models/final_total_model.py
Test-Path src/models/preprocessor.py
Test-Path src/models/train_week1_model.py
Test-Path src/models/artifacts/week1_model.pkl
Test-Path src/models/artifacts/final_total/model.booster.json
Test-Path src/data/numero.duckdb
Test-Path src/frontend/assets/styles.css
```

#### 2. Verify Dependencies
```powershell
# Check if all required packages are installed
pip list | Select-String "streamlit|fastapi|duckdb|pydantic-ai|xgboost"
```

---

### Test Suite

#### 🔹 Test 1: Database Connectivity
**Purpose**: Verify DuckDB can be accessed from new paths

```powershell
# From project root, run:
python -c "import duckdb; conn = duckdb.connect('src/data/numero.duckdb', read_only=True); print('✓ Database connected'); print(f'Tables: {conn.execute(\"SHOW TABLES\").fetchall()}'); conn.close()"
```

**Expected Output**: 
```
✓ Database connected
Tables: [('films_raw',)]
```

**Fix if fails**: Update `DB_PATH` variables in:
- `src/frontend/app.py` (line ~31)
- `src/models/train_week1_model.py` (line ~14)
- `src/utils/data_explorer.py` (line ~6)

---

#### 🔹 Test 2: Import Structure
**Purpose**: Verify all Python imports work correctly

```powershell
# Test frontend imports
python -c "from src.frontend.prompts import sys_prompt, answer_sys; print('✓ Frontend prompts import OK')"

# Test model imports
python -c "from src.models.week1_model import BoxOfficeModel; print('✓ Week1 model import OK')"
python -c "from src.models.final_total_model import FinalTotalPredictor; print('✓ Final total model import OK')"
python -c "from src.models.preprocessor import BoxOfficePreprocessor; print('✓ Preprocessor import OK')"

# Test API imports
python -c "from src.api.server import app; print('✓ API server import OK')"

# Test utils imports
python -c "from src.utils.data_explorer import get_tables; print('✓ Utils import OK')"
```

**Expected Output**: All lines showing "✓ ... import OK"

**Fix if fails**: 
- Add missing `__init__.py` files
- Update import statements to use `src.` prefix
- Check for circular imports

---

#### 🔹 Test 3: Model Artifacts Loading
**Purpose**: Verify ML models can load their saved artifacts

```powershell
# Test Week 1 model loading
python -c "import pickle; f = open('src/models/artifacts/week1_model.pkl', 'rb'); data = pickle.load(f); f.close(); print('✓ Week1 model artifact loaded'); print(f'Keys: {list(data.keys())}')"

# Test Final Total model loading
python -c "from src.models.final_total_model import FinalTotalPredictor; predictor = FinalTotalPredictor('src/models/artifacts/final_total'); predictor.load(); print('✓ Final total model loaded'); print(f'Metadata: {predictor.get_metadata()}')"
```

**Expected Output**:
```
✓ Week1 model artifact loaded
Keys: ['model', 'preprocessor', 'distributor_stats']
✓ Final total model loaded
Metadata: {...}
```

**Fix if fails**: Update paths in model loading code

---

#### 🔹 Test 4: Week 1 Model Prediction
**Purpose**: Test end-to-end Week 1 prediction functionality

```powershell
# Create test_week1.py file with this content:
```
```python
# test_week1.py
from src.models.week1_model import BoxOfficeModel
import pickle

# Load model
with open('src/models/artifacts/week1_model.pkl', 'rb') as f:
    data = pickle.load(f)

model = BoxOfficeModel(
    model=data['model'],
    preprocessor=data['preprocessor'],
    distributor_stats=data.get('distributor_stats', {})
)

# Test prediction
test_input = {
    'censorRating': 'PG',
    'distributorName': 'Universal Pictures',
    'week_date': '2024-06-15',
    'concurrent_films': []
}

result = model.predict_from_json(test_input)
print(f'✓ Week 1 prediction successful')
print(f'Predicted gross: ${result:,.2f}')
```
```powershell
# Run the test
python test_week1.py
```

**Expected Output**: 
```
✓ Week 1 prediction successful
Predicted gross: $X,XXX,XXX.XX
```

**Fix if fails**: 
- Check preprocessor feature names match
- Verify distributor_stats are loaded correctly
- Update model artifact paths

---

#### 🔹 Test 5: Final Total Model Prediction
**Purpose**: Test XGBoost final total prediction

```powershell
# Create test_final.py file with this content:
```
```python
# test_final.py
from src.models.final_total_model import FinalTotalPredictor

predictor = FinalTotalPredictor('src/models/artifacts/final_total')
predictor.load()

test_input = {'wk1_total': 5000000.0}
result = predictor.predict_one(test_input)

print(f'✓ Final total prediction successful')
print(f'Predicted final gross: ${result:,.2f}')
```
```powershell
# Run the test
python test_final.py
```

**Expected Output**:
```
✓ Final total prediction successful
Predicted final gross: $XX,XXX,XXX.XX
```

**Fix if fails**: Check XGBoost model path in `FinalTotalPredictor`

---

#### 🔹 Test 6: FastAPI Server
**Purpose**: Verify API endpoints work correctly

```powershell
# Start the server (in one terminal)
# NOTE: Update Procfile first if needed
uvicorn src.api.server:app --reload --port 8000
```

**In another terminal, test endpoints**:
```powershell
# Test health check
curl http://localhost:8000/

# Test predict1 endpoint
curl -X POST http://localhost:8000/predict1 `
  -H "Content-Type: application/json" `
  -d '{\"censorRating\":\"PG\",\"distributorName\":\"Universal Pictures\",\"week_date\":\"2024-06-15\",\"concurrent_films\":[]}'

# Test predict2 endpoint
curl -X POST http://localhost:8000/predict2 `
  -H "Content-Type: application/json" `
  -d '{\"wk1_total\":5000000.0}'
```

**Expected Output**:
```json
{"message":"BoxOfficeModel FastAPI is running."}
{"predicted_gross":XXXXX.XX}
{"predicted_gross":XXXXX.XX}
```

**Fix if fails**:
- Update model artifact paths in `src/api/server.py` (line ~48)
- Update Procfile: `web: gunicorn -k uvicorn.workers.UvicornWorker src.api.server:app`
- Check import statements

---

#### 🔹 Test 7: Streamlit Frontend
**Purpose**: Test the main chatbot application

```powershell
# Run Streamlit app (from project root)
python -m streamlit run src/frontend/app.py
```

**Manual Tests in Browser**:

1. **CSS Loading Test**
   - Check if custom styles are applied
   - If not, update CSS path in `app.py` line ~28

2. **Database Query Test**
   - Enter: "Show me the top 5 films by weekend gross"
   - Verify SQL generates and returns results

3. **Australian Location Test**
   - Enter: "What is the capital of Queensland?"
   - Should return: "Brisbane"

4. **Week 1 Prediction Test**
   - Enter: "Predict the first week gross for a PG film from Disney releasing on 2024-06-15"
   - Should return prediction with formatted currency

5. **Final Total Prediction Test**
   - Enter: "If a film makes $3 million in week 1, what will be the final total?"
   - Should return final prediction

**Fix if fails**:
- CSS path: Update to `src/frontend/assets/styles.css`
- DB path: Update to `src/data/numero.duckdb`
- Import errors: Fix relative imports in `app.py`
- Prediction endpoints: Check URL configuration

---

#### 🔹 Test 8: Data Explorer Utility
**Purpose**: Test database viewer utility

```powershell
python -m streamlit run src/utils/data_explorer.py
```

**Expected**: 
- Shows database tables
- Can download CSV/JSON exports
- No import errors

**Fix if fails**: Update DB_PATH in `data_explorer.py`

---

#### 🔹 Test 9: Training Script (Optional)
**Purpose**: Verify model can be retrained

```powershell
# WARNING: This will overwrite existing model
# Only run if you have backups or want to retrain

python src/models/train_week1_model.py
```

**Expected Output**:
```
=== Running Randomized Search for ExtraTreeRegressor ===
Best Parameters: ...
Best MAPE: ...
Model saved to src/models/artifacts/week1_model.pkl
```

**Fix if fails**: 
- Update DB_PATH in training script
- Update model save path (line ~143)

---

### Critical Path Configurations

These paths **must** be updated if they haven't been already:

#### 📄 `src/frontend/app.py`
```python
# Line ~22-28: CSS loading
load_css("src/frontend/assets/styles.css")  # Update this path

# Line ~31: Database path
DB_PATH = "src/data/numero.duckdb"  # Update this path
```

#### 📄 `src/api/server.py`
```python
# Line ~48: Model loading
with open("src/models/artifacts/week1_model.pkl", "rb") as f:

# Line ~82: Final total model
final_total_predictor = FinalTotalPredictor("src/models/artifacts/final_total")
```

#### 📄 `Procfile`
```
web: gunicorn -k uvicorn.workers.UvicornWorker src.api.server:app
```

#### 📄 `src/models/train_week1_model.py`
```python
# Line ~14: Database path
DB_PATH = 'src/data/numero.duckdb'

# Line ~143: Model save path
with open('src/models/artifacts/week1_model.pkl', 'wb') as f:
```

#### 📄 `src/utils/data_explorer.py`
```python
# Line ~6: Database path
DB_PATH = 'src/data/numero.duckdb'
```

---

### Environment Variables Check

```powershell
# Verify OpenAI API key is set
$env:OPENAI_API_KEY
```

If not set:
```powershell
# Set temporarily
$env:OPENAI_API_KEY = "your-key-here"

# Or create .env file in project root
@"
OPENAI_API_KEY=your-key-here
"@ | Out-File -Encoding utf8 .env
```

---

### Quick Health Check Script

Save this as `smoke_test.py` for quick verification:

```python
# smoke_test.py
import os
import sys
from pathlib import Path

def test_file_structure():
    """Test 1: File Structure"""
    print("\n📁 Test 1: File Structure...")
    files = [
        "src/frontend/app.py",
        "src/api/server.py",
        "src/models/week1_model.py",
        "src/models/final_total_model.py",
        "src/models/artifacts/week1_model.pkl",
        "src/data/numero.duckdb"
    ]
    all_good = True
    for file in files:
        if Path(file).exists():
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} MISSING")
            all_good = False
    return all_good

def test_database():
    """Test 2: Database Connection"""
    print("\n🗄️  Test 2: Database Connection...")
    try:
        import duckdb
        conn = duckdb.connect('src/data/numero.duckdb', read_only=True)
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"  ✓ Database connected")
        print(f"  Tables: {tables}")
        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False

def test_imports():
    """Test 3: Python Imports"""
    print("\n📦 Test 3: Python Imports...")
    imports = [
        ("from src.frontend.prompts import sys_prompt", "Frontend prompts"),
        ("from src.models.week1_model import BoxOfficeModel", "Week1 model"),
        ("from src.models.final_total_model import FinalTotalPredictor", "Final total model"),
        ("from src.api.server import app", "API server")
    ]
    all_good = True
    for import_stmt, desc in imports:
        try:
            exec(import_stmt)
            print(f"  ✓ {desc}")
        except Exception as e:
            print(f"  ✗ {desc} failed: {e}")
            all_good = False
    return all_good

def test_model_loading():
    """Test 4: Model Loading"""
    print("\n🤖 Test 4: Model Loading...")
    try:
        from src.models.final_total_model import FinalTotalPredictor
        p = FinalTotalPredictor('src/models/artifacts/final_total')
        p.load()
        print("  ✓ Models loaded successfully")
        return True
    except Exception as e:
        print(f"  ✗ Model loading failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 BoxAI Smoke Test Suite\n")
    
    results = [
        test_file_structure(),
        test_database(),
        test_imports(),
        test_model_loading()
    ]
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All smoke tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
        sys.exit(1)
    print("="*50 + "\n")
```

Run with: `python smoke_test.py`

---

### Troubleshooting Common Issues

#### Issue: ModuleNotFoundError
**Solution**: Make sure you're running from project root and `src` is in Python path
```powershell
$env:PYTHONPATH = "."
```

#### Issue: CSS not loading in Streamlit
**Solution**: Update path in `app.py` to `src/frontend/assets/styles.css`

#### Issue: Model file not found
**Solution**: Verify artifacts are in `src/models/artifacts/` and update paths in code

#### Issue: Database connection error
**Solution**: Update all DB_PATH variables to `src/data/numero.duckdb`

#### Issue: API import errors
**Solution**: Update Procfile and import statements to use `src.api.server:app`

---

## 🎯 Conclusion

The BoxAI project is a well-designed film analytics and prediction system with powerful ML capabilities. The recommended restructuring will:

1. **Improve Maintainability**: Clear separation of concerns
2. **Enhance Collaboration**: Easy for team members to navigate
3. **Enable Scaling**: Structure supports adding new features
4. **Facilitate Testing**: Clear test boundaries
5. **Better Documentation**: Organized notebooks and docs

This restructuring aligns with Python best practices and will make the project more professional and easier to work with for both current and future developers.

**After reorganization, use the smoke testing plan above to verify all components work correctly.**
