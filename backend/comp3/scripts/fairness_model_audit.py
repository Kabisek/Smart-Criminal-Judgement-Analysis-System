#!/usr/bin/env python3
"""
Model fairness audit by subgroup using predicted vs actual outcomes.

This script evaluates the existing trained model on the available matrix files
(`X_train_improved.csv`, `y_train_improved.npy`) and joins slices from
`dataset_cleaned_v2.csv` by row order up to min length.

Outputs JSON with:
- overall metrics
- per-slice metrics for offence, court, and year
- minority class (`Partly_Allowed`) precision/recall per slice
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support


def _load_pickle(path: Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def _metrics(y_true: np.ndarray, y_pred: np.ndarray, classes: List[str]) -> Dict[str, float]:
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    acc = float(accuracy_score(y_true, y_pred))

    target = "Partly_Allowed"
    if target in classes:
        target_idx = classes.index(target)
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=[target_idx], average=None, zero_division=0
        )
        partly_precision = float(p[0])
        partly_recall = float(r[0])
        partly_f1 = float(f[0])
    else:
        partly_precision = 0.0
        partly_recall = 0.0
        partly_f1 = 0.0

    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "partly_precision": round(partly_precision, 4),
        "partly_recall": round(partly_recall, 4),
        "partly_f1": round(partly_f1, 4),
    }


def _slice_report(
    df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: List[str],
    slice_col: str,
    top_n: int,
    min_n: int,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    values = df[slice_col].fillna("Unknown").astype(str).replace("", "Unknown")
    for key in values.value_counts().head(top_n).index.tolist():
        idx = values[values == key].index.to_numpy()
        if len(idx) == 0:
            continue
        m = _metrics(y_true[idx], y_pred[idx], classes)
        out.append(
            {
                "slice_value": str(key),
                "n": int(len(idx)),
                "low_sample": bool(len(idx) < min_n),
                **m,
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Predicted-vs-actual subgroup fairness audit.")
    parser.add_argument("--comp3-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--min-n", type=int, default=25, help="Flag slices below this sample size.")
    parser.add_argument("--top", type=int, default=40, help="Max slices per dimension.")
    parser.add_argument("--out", type=Path, default=None, help="Write report JSON to file.")
    args = parser.parse_args()

    comp3 = args.comp3_dir
    model = _load_pickle(comp3 / "improved_ensemble_model.pkl")
    scaler = _load_pickle(comp3 / "improved_scaler.pkl")
    label_encoder = _load_pickle(comp3 / "improved_label_encoder.pkl")
    selected_features = _load_pickle(comp3 / "improved_selected_features.pkl")

    X = pd.read_csv(comp3 / "X_train_improved.csv")
    y_true = np.load(comp3 / "y_train_improved.npy")
    df = pd.read_csv(comp3 / "dataset_cleaned_v2.csv")

    # Align by shortest length because matrix files may represent a subset/split.
    n = min(len(X), len(y_true), len(df))
    X = X.iloc[:n].copy()
    y_true = np.asarray(y_true[:n], dtype=int)
    df = df.iloc[:n].copy()

    X_model = X[list(selected_features)].copy().fillna(0.0)
    X_scaled = scaler.transform(X_model)
    X_scaled_df = pd.DataFrame(X_scaled, columns=list(selected_features))
    y_pred = np.asarray(model.predict(X_scaled_df), dtype=int)
    classes = [str(c) for c in label_encoder.classes_]

    # Standardized slice columns used by this audit.
    if "offence_category_grouped" not in df.columns:
        df["offence_category_grouped"] = df.get("offence_category", "Unknown")
    if "high_court_location" not in df.columns:
        df["high_court_location"] = "Unknown"
    if "coa_year" not in df.columns:
        df["coa_year"] = "Unknown"

    report: Dict[str, Any] = {
        "dataset_rows_used": int(n),
        "slice_min_n": int(args.min_n),
        "labels": classes,
        "overall": _metrics(y_true, y_pred, classes),
        "by_offence_group": _slice_report(
            df=df,
            y_true=y_true,
            y_pred=y_pred,
            classes=classes,
            slice_col="offence_category_grouped",
            top_n=args.top,
            min_n=args.min_n,
        ),
        "by_high_court": _slice_report(
            df=df,
            y_true=y_true,
            y_pred=y_pred,
            classes=classes,
            slice_col="high_court_location",
            top_n=args.top,
            min_n=args.min_n,
        ),
        "by_year": _slice_report(
            df=df,
            y_true=y_true,
            y_pred=y_pred,
            classes=classes,
            slice_col="coa_year",
            top_n=args.top,
            min_n=args.min_n,
        ),
        "notes": [
            "This is a model-performance subgroup report (predicted vs actual).",
            "Rows are aligned by order up to min(len(X_train), len(y_train), len(dataset)).",
            "Slices with low_sample=true should be treated as unstable.",
        ],
    }

    payload = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

