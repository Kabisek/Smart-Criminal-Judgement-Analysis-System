#!/usr/bin/env python3
"""
Offline audit: outcome label distribution by offence group, court, and year.

Uses columns from dataset_cleaned_v2.csv (no comp3 package import, so it runs
without loading PyTorch). For court names matching the API dashboard, use
GET /api/v1/appeal/dashboard/fairness-report instead.

Usage (from repository root):
  python backend/comp3/scripts/fairness_slice_audit.py
  python backend/comp3/scripts/fairness_slice_audit.py --csv path/to/dataset.csv --min-n 30 --out report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def simplify_outcome(val: str) -> str:
    if isinstance(val, str):
        lower = val.lower()
        if lower.startswith("dismissed"):
            return "Appeal_Dismissed"
        if lower.startswith("allowed"):
            return "Appeal_Allowed"
        if lower.startswith("partly"):
            return "Partly_Allowed"
    return "Other"


def main() -> int:
    here = Path(__file__).resolve()
    default_csv = here.parents[1] / "dataset_cleaned_v2.csv"

    parser = argparse.ArgumentParser(description="Label-distribution audit by slice (corpus balance, not model error).")
    parser.add_argument("--csv", type=Path, default=default_csv, help="Path to dataset CSV")
    parser.add_argument("--min-n", type=int, default=25, dest="min_n", help="Flag slices smaller than this")
    parser.add_argument("--out", type=Path, default=None, help="Write JSON to this path")
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if "result_category" not in df.columns:
        if "combined_outcome" in df.columns:
            df["result_category"] = df["combined_outcome"].apply(simplify_outcome)
        else:
            df["result_category"] = "Other"

    if "offence_category_grouped" in df.columns:
        df["_offence_group"] = df["offence_category_grouped"].fillna("Unknown").astype(str).replace("", "Unknown")
    elif "offence_category" in df.columns:
        df["_offence_group"] = df["offence_category"].fillna("Unknown").astype(str).replace("", "Unknown")
    else:
        df["_offence_group"] = "Unknown"

    if "high_court_location" in df.columns:
        df["_court"] = df["high_court_location"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    else:
        df["_court"] = "Unknown"

    total = len(df)
    oc = df["result_category"].value_counts().to_dict()

    def slice_table(group_col: str, top: int = 40) -> list:
        rows = []
        for key in df[group_col].value_counts().head(top).index.tolist():
            grp = df[df[group_col] == key]
            n = int(len(grp))
            counts = grp["result_category"].value_counts().to_dict()
            a = int(counts.get("Appeal_Allowed", 0))
            p = int(counts.get("Partly_Allowed", 0))
            d = int(counts.get("Appeal_Dismissed", 0))
            rows.append(
                {
                    "slice_value": str(key),
                    "n": n,
                    "appeal_allowed_pct": round(100 * a / n, 2) if n else 0.0,
                    "partly_allowed_pct": round(100 * p / n, 2) if n else 0.0,
                    "appeal_dismissed_pct": round(100 * d / n, 2) if n else 0.0,
                    "low_sample": n < args.min_n,
                }
            )
        return rows

    by_year: list = []
    if "coa_year" in df.columns:
        for y in sorted(df["coa_year"].dropna().unique().tolist()):
            try:
                yi = int(y)
            except (TypeError, ValueError):
                continue
            grp = df[df["coa_year"] == y]
            n = int(len(grp))
            counts = grp["result_category"].value_counts().to_dict()
            a = int(counts.get("Appeal_Allowed", 0))
            p = int(counts.get("Partly_Allowed", 0))
            d = int(counts.get("Appeal_Dismissed", 0))
            by_year.append(
                {
                    "year": yi,
                    "n": n,
                    "appeal_allowed_pct": round(100 * a / n, 2) if n else 0.0,
                    "partly_allowed_pct": round(100 * p / n, 2) if n else 0.0,
                    "appeal_dismissed_pct": round(100 * d / n, 2) if n else 0.0,
                    "low_sample": n < args.min_n,
                }
            )

    report = {
        "dataset_rows": total,
        "min_slice_n": args.min_n,
        "overall_counts": {
            k: int(oc.get(k, 0)) for k in ["Appeal_Allowed", "Partly_Allowed", "Appeal_Dismissed", "Other"]
        },
        "by_offence": slice_table("_offence_group"),
        "by_court": slice_table("_court"),
        "by_year": by_year,
        "notes": [
            "Label distribution only; not predictive performance.",
            f"Slices with n < {args.min_n} flagged as low_sample.",
            "Court grouping uses raw high_court_location (API fairness-report uses canonical names).",
        ],
    }

    text = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
