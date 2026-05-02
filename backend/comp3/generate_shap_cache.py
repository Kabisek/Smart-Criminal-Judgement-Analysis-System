"""
Generate offline SHAP explanation cache for Component 3 runtime.

Primary path:
- uses real SHAP values (TreeExplainer) for tree-based estimators in the
  voting ensemble, then aggregates across estimators.

Fallback path:
- uses feature_importances_ weighting if SHAP is unavailable.

Output:
- improved_shap_summary.json
"""

import json
import pickle
import io
import contextlib
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


def _to_2d_class_matrix(shap_vals: Any, class_idx: int, n_features: int) -> np.ndarray:
    """
    Normalize SHAP outputs to shape (n_samples, n_features) for a class.
    Handles list-based and ndarray-based outputs from different SHAP versions.
    """
    if isinstance(shap_vals, list):
        if len(shap_vals) <= class_idx:
            return np.empty((0, n_features), dtype=float)
        arr = np.asarray(shap_vals[class_idx], dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        return arr

    arr = np.asarray(shap_vals, dtype=float)
    # Could be (samples, features, classes) or (classes, samples, features)
    if arr.ndim == 3:
        if arr.shape[2] > class_idx:
            return arr[:, :, class_idx]
        if arr.shape[0] > class_idx:
            return arr[class_idx, :, :]
    if arr.ndim == 2:
        return arr
    if arr.ndim == 1:
        return arr.reshape(1, -1)
    return np.empty((0, n_features), dtype=float)


def _safe_import_shap():
    """
    Import SHAP quietly. Some environments print binary-compat warnings to stderr.
    """
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            import shap  # type: ignore
        return shap
    except BaseException:
        return None


def _compute_real_shap(
    model: Any,
    feature_names: List[str],
    X_sample: pd.DataFrame,
    class_idx: int,
    shap_module: Any,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    Compute aggregated SHAP summaries across tree estimators in ensemble.
    """
    if not hasattr(model, "estimators_"):
        raise RuntimeError("Model has no estimators_ for tree SHAP aggregation.")

    global_abs_acc = np.zeros(len(feature_names), dtype=float)
    local_signed_acc = np.zeros(len(feature_names), dtype=float)
    used_estimators = 0

    # Global uses up to 120 rows for speed.
    X_bg = X_sample.iloc[: min(len(X_sample), 120)].copy()
    X_one = X_sample.iloc[[0]].copy()

    for est in model.estimators_:
        try:
            explainer = shap_module.TreeExplainer(est)
            sv_bg = explainer.shap_values(X_bg)
            sv_one = explainer.shap_values(X_one)

            bg_mat = _to_2d_class_matrix(sv_bg, class_idx=class_idx, n_features=len(feature_names))
            one_mat = _to_2d_class_matrix(sv_one, class_idx=class_idx, n_features=len(feature_names))
            if bg_mat.size == 0 or one_mat.size == 0:
                continue

            global_abs_acc += np.mean(np.abs(bg_mat), axis=0)
            local_signed_acc += one_mat[0]
            used_estimators += 1
        except Exception:
            # skip estimators unsupported by TreeExplainer
            continue

    if used_estimators == 0:
        raise RuntimeError("No estimator produced valid TreeExplainer SHAP output.")

    global_abs = global_abs_acc / used_estimators
    local_signed = local_signed_acc / used_estimators

    global_total = float(np.sum(global_abs)) + 1e-12
    global_norm = global_abs / global_total

    global_rank = np.argsort(-np.abs(global_norm))[:top_n]
    local_rank = np.argsort(-np.abs(local_signed))[: min(10, len(feature_names))]

    global_top = [
        {"feature": feature_names[i], "importance": float(global_norm[i])}
        for i in global_rank
    ]
    local_top = [
        {
            "feature": feature_names[i],
            "contribution": float(local_signed[i]),
            "abs_contribution": float(abs(local_signed[i])),
            "value": float(X_one.iloc[0, i]),
        }
        for i in local_rank
    ]

    return {
        "method": "real_shap_treeexplainer_ensemble_avg",
        "estimators_used": used_estimators,
        "global_top": global_top,
        "local_top": local_top,
    }


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

    # Determine target class index for local explanation
    pred_class_idx = 0
    try:
        pred_class_idx = int(model.predict(X.iloc[[0]])[0])
    except Exception:
        pred_class_idx = 0

    # Try real SHAP first.
    method_details: Dict[str, Any] = {}
    try:
        shap_module = _safe_import_shap()
        if shap_module is None:
            raise RuntimeError("SHAP import unavailable in this environment.")
        real = _compute_real_shap(
            model=model,
            feature_names=feature_names,
            X_sample=X,
            class_idx=pred_class_idx,
            shap_module=shap_module,
            top_n=20,
        )
        global_top = real["global_top"]
        local_top = real["local_top"]
        method = real["method"]
        method_details = {"estimators_used": real.get("estimators_used", 0)}
    except Exception as e:
        # Fallback: feature importance proxy
        importance = _get_feature_importance(model, feature_names)
        if len(importance) != len(feature_names):
            importance = np.ones(len(feature_names), dtype=float) / max(len(feature_names), 1)
        norm_imp = importance / (np.sum(np.abs(importance)) + 1e-12)
        global_rank = np.argsort(-np.abs(norm_imp))[:20]
        global_top = [
            {
                "feature": feature_names[i],
                "importance": float(norm_imp[i]),
            }
            for i in global_rank
        ]

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
        method = "tree_importance_weighted_local_proxy"
        method_details = {"fallback_reason": str(e)}

    payload: Dict[str, Any] = {
        "version": "v2_offline_cached",
        "method": method,
        "method_details": method_details,
        "global_summary": {
            "top_global_features": global_top
        },
        "prediction_summary": {
            "target_class_index": pred_class_idx,
            "top_feature_contributions": local_top
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Saved SHAP-style cache: {output_path}")


if __name__ == "__main__":
    main()

