# BoxAI Repository Guide

This guide orients new collaborators to the repo layout, what each folder/file does, and where to add new work.
```
boxai/
  README.md                 
  ways-of-working.md        
  requirements.txt           # Python dependencies 
  identifier.db              # Local database / reference store (legacy)
  data/                      # Source data (raw inputs only)
  src/                       # Reusable Python package code
    boxai/
      models/
        final_total_predictor.py
  notebooks/                 
    exploration/
      Data_Wrangling.ipynb
    modeling/
      01_baseline_final_total.ipynb
      02_xgb_model_week2.ipynb
    inference/
      FinalTotal_Inference.ipynb
    legacy/
      XGB_Model_legacy.ipynb
  experiments/
    final_total_baseline/    # Saved artifacts for a specific trained run
      model.booster.json
      schema.json
      training_metrics.json
      metadata.json
  docs/
    repository_guide.md      
  .gitignore
```

## 2. Folder Purposes
* `README.md` – High-level narrative & goals.
* `ways-of-working.md` – Team process & collaboration norms.
* `data/` – Local data inputs (source datasets only).
* `src/` – Reusable importable project code (models, utilities).
* `notebooks/` – Exploration, modelling, inference demos.
* `notebooks/exploration/` – Data understanding & wrangling.
* `notebooks/modeling/` – Training / evaluation experiments.
* `notebooks/inference/` – Example prediction usage.
* `notebooks/legacy/` – Archived older notebooks.
* `experiments/` – Saved model run artifacts (immutable snapshots).
* `docs/` – Supplemental documentation & guides.

## 3. Key Artifact Files (Experiment Run)
* `model.booster.json` – Serialized XGBoost model used for inference.
* `schema.json` – Feature contract & transforms.
* `training_metrics.json` – Evaluation results.
* `metadata.json` – Run provenance (timestamp, parameters, iterations).

## 4. Predictor Module (`final_total_predictor.py`)
Responsibilities:
- Load booster and supporting JSON files
- Validate inputs (non‑negative `wk1_total`)
- Apply log1p → predict in log space → expm1 back-transform
- Single value and batch prediction methods
- Static save helper for future integration with training pipelines

Add another predictor for a new target by copying the pattern (e.g. `wk2_weekly_predictor.py`).

## 5. Typical Workflows
### A. Baseline Model Iteration
1. Open `notebooks/modeling/01_baseline_final_total.ipynb`.
2. Adjust hyperparameters or simple feature transforms.
3. Save new artifacts to `experiments/final_total_<descriptor>/`.
4. Commit the new experiment folder.

### B. Add a New Target (e.g. week 2 weekly)
1. Duplicate notebook → `03_baseline_wk2_weekly.ipynb`.
2. Train & save artifacts to `experiments/wk2_weekly_baseline/`.
3. Create `src/boxai/models/wk2_weekly_predictor.py`.
4. Add an inference notebook under `notebooks/inference/` if needed.

### C. Use Model for Inference
```python
import sys, os
sys.path.append(os.path.abspath("src"))
from boxai.models.final_total_predictor import FinalTotalPredictor
p = FinalTotalPredictor("experiments/final_total_baseline")
print(p.predict_one({"wk1_total": 12000}))
```


_Last updated: 2025-10-02_
