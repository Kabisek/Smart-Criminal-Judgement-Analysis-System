#!/usr/bin/env python3
"""
Batch-evaluate Component 3 predictions against raw_inputs.json ground truth.

Requires the FastAPI backend running (default http://127.0.0.1:8000).

Usage (from repo root):
  python backend/comp3/input_test_cases/run_batch_eval.py
  set COMP3_API_BASE=http://127.0.0.1:8000 && python backend/comp3/input_test_cases/run_batch_eval.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
RAW_JSON = HERE / "raw_inputs.json"
DEFAULT_BASE = os.environ.get("COMP3_API_BASE", "http://127.0.0.1:8000").rstrip("/")
PREDICT_URL = f"{DEFAULT_BASE}/api/v1/appeal/predict"


def _post_predict(case_description: str) -> Dict[str, Any]:
    body = json.dumps({"case_description": case_description}).encode("utf-8")
    req = urllib.request.Request(
        PREDICT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    if not RAW_JSON.exists():
        print(f"Missing {RAW_JSON}", file=sys.stderr)
        return 1

    cases: List[Dict[str, Any]] = json.loads(RAW_JSON.read_text(encoding="utf-8"))
    rows_out: List[Dict[str, Any]] = []
    correct = 0
    comparable = 0

    print(f"API: {PREDICT_URL}")
    print(f"Cases: {len(cases)}\n")

    for i, c in enumerate(cases):
        text = c.get("application_input_paragraph") or ""
        truth = (c.get("final_appeal_decision") or "").strip()
        cid = c.get("conversion_id") or f"case_{i}"

        if truth in ("", "Not_Available", "Unknown"):
            rows_out.append(
                {
                    "conversion_id": cid,
                    "truth": truth,
                    "predicted": "SKIP",
                    "match": False,
                    "confidence": None,
                    "error": f"ground truth not comparable: {truth or 'empty'}",
                }
            )
            print(f"[{i + 1}/{len(cases)}] {cid} SKIP (truth={truth})")
            continue

        if len(text.strip()) < 50:
            rows_out.append(
                {
                    "conversion_id": cid,
                    "truth": truth,
                    "predicted": "SKIP",
                    "match": False,
                    "confidence": None,
                    "error": "input shorter than 50 chars",
                }
            )
            print(f"[{i + 1}/{len(cases)}] {cid} SKIP (<50 chars)")
            continue

        try:
            res = _post_predict(text)
            pred = (res.get("prediction") or "").strip()
            conf = res.get("confidence")
            abstained = bool(res.get("abstained", False))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:500]
            rows_out.append(
                {
                    "conversion_id": cid,
                    "truth": truth,
                    "predicted": None,
                    "match": False,
                    "confidence": None,
                    "error": f"HTTP {e.code}: {err_body}",
                }
            )
            print(f"[{i + 1}/{len(cases)}] {cid} HTTP ERROR {e.code}")
            continue
        except Exception as e:
            rows_out.append(
                {
                    "conversion_id": cid,
                    "truth": truth,
                    "predicted": None,
                    "match": False,
                    "confidence": None,
                    "error": str(e),
                }
            )
            print(f"[{i + 1}/{len(cases)}] {cid} ERROR: {e}")
            continue

        # Domain abstention / non-standard label: don't count toward accuracy
        if pred == "Insufficient_Legal_Context":
            match = False
            counted = False
        else:
            counted = pred in ("Appeal_Allowed", "Appeal_Dismissed", "Partly_Allowed")
            match = counted and (pred == truth)
            if counted:
                comparable += 1
                if match:
                    correct += 1

        rows_out.append(
            {
                "conversion_id": cid,
                "truth": truth,
                "predicted": pred,
                "match": match,
                "confidence": conf,
                "abstained": abstained,
                "counted_for_accuracy": counted,
                "error": None,
            }
        )
        sym = "OK" if match else "X "
        print(f"[{i + 1}/{len(cases)}] {cid} truth={truth} pred={pred} ({sym}) conf={conf}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = HERE / f"eval_results_{ts}.csv"

    # Simple CSV
    import csv

    if rows_out:
        keys = list(rows_out[0].keys())
        with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in rows_out:
                w.writerow(r)

    print()
    print(f"Compared (standard labels only): {comparable}")
    print(f"Correct: {correct}")
    if comparable:
        print(f"Accuracy: {100.0 * correct / comparable:.2f}%")
    print(f"Wrote: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
