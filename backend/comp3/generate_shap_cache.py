"""
Generate offline SHAP-style explanation cache for Component 3 runtime.

This script computes:
- global feature importance (tree-ensemble feature_importances_ fallback)
- sample-level top contributing features (approximate contribution using
  absolute standardized feature values weighted by global importance)

Output:
- improved_shap_summary.json
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd


COMP3_DIR = Path(__file__).resolve().parent


def _load_pickle(path: Path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _get_feature_importance(model, feature_names: List[str]) -> np.ndarray:
    # VotingClassifier: aggregate importances from estimators that expose feature_importances_
    if hasattr(model, "estimators_"):
        importances = []
        for est in model.estimators_:
            if hasattr(est, "feature_importances_"):
                importances.append(np.asarray(est.feature_importances_, dtype=float))
        if importances:
            return np.mean(np.vstack(importances), axis=0)
    # Direct model path
    if hasattr(model, "feature_importances_"):
        return np.asarray(model.feature_importances_, dtype=float)
    # Fallback uniform weights
    return np.ones(len(feature_names), dtype=float) / max(len(feature_names), 1)


def main():
    x_train_path = COMP3_DIR / "X_train_improved.csv"
    model_path = COMP3_DIR / "improved_ensemble_model.pkl"
    selected_features_path = COMP3_DIR / "improved_selected_features.pkl"
    output_path = COMP3_DIR / "improved_shap_summary.json"

    X_train = pd.read_csv(x_train_path)
    model = _load_pickle(model_path)
    selected_features = _load_pickle(selected_features_path)

    feature_names = list(selected_features)
    X = X_train[feature_names].copy()

    importance = _get_feature_importance(model, feature_names)
    if len(importance) != len(feature_names):
        importance = np.ones(len(feature_names), dtype=float) / max(len(feature_names), 1)

    norm_imp = importance / (np.sum(np.abs(importance)) + 1e-12)

    # Global top features
    global_rank = np.argsort(-np.abs(norm_imp))[:20]
    global_top = [
        {
            "feature": feature_names[i],
            "importance": float(norm_imp[i]),
        }
        for i in global_rank
    ]

    # Approx sample contributions: abs(value) * abs(global_importance)
    row = X.iloc[0].to_numpy(dtype=float)
    contrib = np.abs(row) * np.abs(norm_imp)
    row_rank = np.argsort(-contrib)[:10]
    local_top = [
        {
            "feature": feature_names[i],
            "contribution": float(contrib[i]),
            "value": float(row[i]),
        }
        for i in row_rank
    ]

    payload: Dict[str, Any] = {
        "version": "v1_offline_cached",
        "method": "tree_importance_weighted_local_proxy",
        "global_summary": {
            "top_global_features": global_top
        },
        "prediction_summary": {
            "top_feature_contributions": local_top
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved SHAP-style cache: {output_path}")


if __name__ == "__main__":
    main()

