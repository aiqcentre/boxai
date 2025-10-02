from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import xgboost as xgb
import pandas as pd


@dataclass
class _BestInfo:
    best_ntree_limit: Optional[int]
    best_iteration: Optional[int]


class FinalTotalPredictor:
    """Predictor for `final_total` from `wk1_total` using a saved XGBoost Booster.

    Workflow:
        predictor = FinalTotalPredictor("artifacts/final_total")
        predictor.load()
        y = predictor.predict_one({"wk1_total": 12345})

    Assumptions:
        - Single numeric non-negative feature: wk1_total
        - log1p transform applied to feature during inference and training
        - Target predicted in log space then inverse transformed via expm1
    """

    MODEL_FILE = "model.booster.json"
    METADATA_FILE = "metadata.json"
    SCHEMA_FILE = "schema.json"
    METRICS_FILE = "training_metrics.json"

    def __init__(self, artifacts_dir: str, lazy: bool = False) -> None:
        self.artifacts_dir = artifacts_dir
        self._booster: Optional[xgb.Booster] = None
        self._best_info: _BestInfo | None = None
        self._metadata: Dict[str, Any] | None = None
        self._schema: Dict[str, Any] | None = None
        if not lazy:
            self.load()

    # ------------------------------- Public API -------------------------------
    def load(self) -> None:
        """Load booster, metadata, and schema from artifacts directory."""
        model_path = os.path.join(self.artifacts_dir, self.MODEL_FILE)
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        booster = xgb.Booster()
        booster.load_model(model_path)
        self._booster = booster

        metadata_path = os.path.join(self.artifacts_dir, self.METADATA_FILE)
        if os.path.isfile(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {}

        schema_path = os.path.join(self.artifacts_dir, self.SCHEMA_FILE)
        if os.path.isfile(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        else:
            # Fallback default schema
            self._schema = {
                "features": {
                    "wk1_total": {"type": "float", "required": True, "allow_null": False, "min": 0}
                }
            }

        best_ntree_limit = self._metadata.get("best_ntree_limit") if self._metadata else None
        best_iteration = self._metadata.get("best_iteration") if self._metadata else None
        self._best_info = _BestInfo(best_ntree_limit=best_ntree_limit, best_iteration=best_iteration)

    def predict_one(self, record: Dict[str, Any]) -> float:
        """Predict a single value from a record dict containing `wk1_total`.

        Parameters
        ----------
        record : dict
            Must contain the key 'wk1_total'. Value must be numeric and non-negative.
        """
        self._ensure_loaded()
        value = self._validate_and_extract(record)
        arr = np.array([[value]], dtype="float64")
        log_arr = np.log1p(arr)
        dmat = xgb.DMatrix(log_arr)
        pred_log = self._predict_internal(dmat)
        pred = np.expm1(pred_log)[0]
        return float(pred)

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Batch predict from a DataFrame containing column `wk1_total`.

        Returns a pandas Series with index aligned to input.
        """
        self._ensure_loaded()
        if "wk1_total" not in df.columns:
            raise ValueError("Input DataFrame missing required column 'wk1_total'")
        col = df["wk1_total"].astype("float64")
        if col.isna().any():
            raise ValueError("Column 'wk1_total' contains NaN values")
        if (col < 0).any():
            raise ValueError("Column 'wk1_total' contains negative values")
        arr = col.to_numpy().reshape(-1, 1)
        log_arr = np.log1p(arr)
        dmat = xgb.DMatrix(log_arr)
        pred_log = self._predict_internal(dmat)
        preds = np.expm1(pred_log)
        return pd.Series(preds, index=df.index, name="final_total_pred")

    def get_metadata(self) -> Dict[str, Any]:
        self._ensure_loaded()
        return dict(self._metadata) if self._metadata else {}

    # ------------------------------ Class Methods -----------------------------
    @classmethod
    def save_from_training(
        cls,
        booster: xgb.Booster,
        artifacts_dir: str,
        best_ntree_limit: Optional[int] = None,
        best_iteration: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None,
        overwrite: bool = True,
    ) -> None:
        """Persist a trained booster and associated metadata/schema.

        Parameters
        ----------
        booster : xgb.Booster
            Trained booster.
        artifacts_dir : str
            Directory to store artifacts.
        best_ntree_limit : int, optional
            Best ntree limit from early stopping.
        best_iteration : int, optional
            Best iteration from early stopping.
        metrics : dict, optional
            Evaluation metrics dict.
        overwrite : bool
            Whether to overwrite existing directory contents.
        """
        os.makedirs(artifacts_dir, exist_ok=True)
        model_path = os.path.join(artifacts_dir, cls.MODEL_FILE)
        if os.path.exists(model_path) and not overwrite:
            raise FileExistsError(f"Model file already exists: {model_path}")
        booster.save_model(model_path)

        metadata = {
            "model_name": "final_total_regressor",
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "objective": booster.attributes().get("objective", "reg:squarederror"),
            "eval_metric": booster.attributes().get("eval_metric", "rmse"),
            "best_ntree_limit": best_ntree_limit,
            "best_iteration": best_iteration,
            "input_feature": "wk1_total",
            "transform": "log1p",
            "inverse_transform": "expm1",
        }
        with open(os.path.join(artifacts_dir, cls.METADATA_FILE), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        schema = {
            "features": {
                "wk1_total": {"type": "float", "required": True, "allow_null": False, "min": 0}
            }
        }
        with open(os.path.join(artifacts_dir, cls.SCHEMA_FILE), "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        if metrics:
            with open(os.path.join(artifacts_dir, cls.METRICS_FILE), "w", encoding="utf-8") as f:
                json.dump({"holdout": metrics}, f, indent=2)

    # ------------------------------ Internal ----------------------------------
    def _ensure_loaded(self) -> None:
        if self._booster is None:
            raise RuntimeError("Model not loaded; call load() first or instantiate with lazy=False")

    def _validate_and_extract(self, record: Dict[str, Any]) -> float:
        if "wk1_total" not in record:
            raise ValueError("Missing required feature 'wk1_total'")
        val = record["wk1_total"]
        try:
            fval = float(val)
        except (TypeError, ValueError):
            raise TypeError("Feature 'wk1_total' must be numeric") from None
        if np.isnan(fval):
            raise ValueError("Feature 'wk1_total' cannot be NaN")
        if fval < 0:
            raise ValueError("Feature 'wk1_total' must be non-negative")
        return fval

    def _predict_internal(self, dmat: xgb.DMatrix) -> np.ndarray:
        assert self._booster is not None
        if self._best_info:
            if self._best_info.best_ntree_limit:
                return self._booster.predict(dmat, ntree_limit=self._best_info.best_ntree_limit)
            if self._best_info.best_iteration is not None:
                return self._booster.predict(dmat, iteration_range=(0, self._best_info.best_iteration + 1))
        return self._booster.predict(dmat)


__all__ = ["FinalTotalPredictor"]
