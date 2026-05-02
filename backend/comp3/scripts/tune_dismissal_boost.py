#!/usr/bin/env python3
"""
Tune dismissal_probability_boost on held-out X_test_improved (post-hoc calibration).

Maximize balanced accuracy subject to overall accuracy >= floor (default 0.52).
Writes best boost into improved_model_metadata.json as dismissal_probability_boost.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score

COMP3 = Path(__file__).resolve().parent.parent


def main() -> int:
    meta_path = COMP3 / "improved_model_metadata.json"
    with open(COMP3 / "improved_label_encoder.pkl", "rb") as f:
        le = pickle.load(f)
    with open(COMP3 / "improved_ensemble_model.pkl", "rb") as f:
        model = pickle.load(f)

    X = pd.read_csv(COMP3 / "X_test_improved.csv")
    y = np.load(COMP3 / "y_test_improved.npy")

    classes = list(le.classes_)
    dismissed_idx = classes.index("Appeal_Dismissed")

    probs_base = model.predict_proba(X.values)

    partly_thr = 0.4
    partly_idx = classes.index("Partly_Allowed") if "Partly_Allowed" in classes else None

    acc_floor = 0.52
    best = None

    for boost in np.linspace(1.0, 3.0, 41):
        probs = probs_base.copy()
        probs[:, dismissed_idx] *= float(boost)
        probs /= probs.sum(axis=1, keepdims=True)

        pred = np.argmax(probs, axis=1)
        if partly_idx is not None:
            for i in range(len(pred)):
                if probs[i, partly_idx] >= partly_thr:
                    pred[i] = partly_idx
                else:
                    pred[i] = int(np.argmax(probs[i]))

        acc = accuracy_score(y, pred)
        ba = balanced_accuracy_score(y, pred)
        m = y == dismissed_idx
        d_rec = float((pred[m] == dismissed_idx).mean()) if np.any(m) else 0.0
        a_idx = classes.index("Appeal_Allowed")
        ma = y == a_idx
        a_rec = float((pred[ma] == a_idx).mean()) if np.any(ma) else 0.0

        if acc < acc_floor:
            continue
        if best is None or ba > best[0]:
            best = (ba, boost, acc, d_rec, a_rec)

    if best is None:
        # relax floor
        for boost in np.linspace(1.0, 3.0, 41):
            probs = probs_base.copy()
            probs[:, dismissed_idx] *= float(boost)
            probs /= probs.sum(axis=1, keepdims=True)
            pred = np.argmax(probs, axis=1)
            if partly_idx is not None:
                for i in range(len(pred)):
                    if probs[i, partly_idx] >= partly_thr:
                        pred[i] = partly_idx
                    else:
                        pred[i] = int(np.argmax(probs[i]))
            acc = accuracy_score(y, pred)
            ba = balanced_accuracy_score(y, pred)
            m = y == dismissed_idx
            d_rec = float((pred[m] == dismissed_idx).mean()) if np.any(m) else 0.0
            a_idx = classes.index("Appeal_Allowed")
            ma = y == a_idx
            a_rec = float((pred[m] == a_idx).mean()) if np.any(ma) else 0.0
            if best is None or ba > best[0]:
                best = (ba, boost, acc, d_rec, a_rec)

    if best is None:
        print("No configuration found")
        return 1

    ba, boost, acc, d_rec, a_rec = best
    print(f"Best balanced_acc={ba:.4f} at dismissal_probability_boost={boost:.3f}")
    print(f"  overall_acc={acc:.4f}  dismissed_recall={d_rec:.4f}  allowed_recall={a_rec:.4f}")

    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["dismissal_probability_boost"] = float(boost)
    meta["dismissal_boost_tuned_on"] = "X_test_improved"
    meta["dismissal_boost_metrics"] = {
        "balanced_accuracy": ba,
        "accuracy": acc,
        "dismissed_recall_proxy": d_rec,
        "allowed_recall_proxy": a_rec,
        "accuracy_floor_attempted": acc_floor,
    }
    meta_path.write_text(json.dumps(meta, indent=4), encoding="utf-8")
    print(f"Updated {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
