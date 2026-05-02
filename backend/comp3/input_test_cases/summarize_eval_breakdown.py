"""Summarize eval CSV by truth class and heuristic offence bucket."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def offence_bucket(text: str) -> str:
    t = (text or "").lower()
    rules: list[tuple[str, list[str]]] = [
        ("Drugs / Dangerous Drugs", [
            r"poisons, opium",
            r"dangerous drugs",
            r"heroin",
            r"54a",
            r"diacetylmorphine",
        ]),
        ("Bribery / Corruption", [
            r"bribery act",
            r"\bbribe\b",
            r"commission to investigate",
        ]),
        ("Sexual offences", [
            r"365b",
            r"grave sexual",
            r"\brape\b",
            r"section 364",
        ]),
        ("Murder / homicide (296)", [
            r"section 296",
            r"\bmurder\b",
        ]),
        ("Robbery / theft / assembly", [
            r"section 380",
            r"robbery",
            r"unlawful assembly",
            r"section 383",
        ]),
        ("Traffic / motor accident", [
            r"motor traffic",
            r"road traffic",
            r"sections 328",
            r"section 328",
            r"section 329",
        ]),
        ("Military / Navy discipline", [
            r"navy act",
            r"summary trial",
            r"naval ",
            r"disciplinary offences",
        ]),
        ("Land / civil / writ / Wakf", [
            r"land development ordinance",
            r"writ of certiorari",
            r"wakf",
            r"mosques and charitable",
            r"state lands \(recovery",
            r"partition",
        ]),
        ("EPF / labour / recovery", [
            r"provident fund",
            r"epf act",
        ]),
    ]
    for name, pats in rules:
        for p in pats:
            if re.search(p, t):
                return name
    return "Other / mixed"


def main() -> None:
    csv_path = HERE / "eval_results_20260502_110829.csv"
    raw = json.loads((HERE / "raw_inputs.json").read_text(encoding="utf-8"))
    by_id = {r["conversion_id"]: r for r in raw}

    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    by_truth: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_bucket: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in rows:
        tid = row["conversion_id"]
        truth = (row["truth"] or "").strip()
        if truth in ("", "Not_Available"):
            continue
        if row.get("counted_for_accuracy") != "True":
            continue
        para = by_id.get(tid, {}).get("application_input_paragraph", "")
        bucket = offence_bucket(para)
        ok = row["match"] == "True"
        by_truth[truth]["total"] += 1
        by_truth[truth]["correct" if ok else "wrong"] += 1
        by_bucket[bucket]["total"] += 1
        by_bucket[bucket]["correct" if ok else "wrong"] += 1

    print("=== Per GOLD (truth) class — counted rows only ===")
    for k in sorted(by_truth.keys()):
        d = by_truth[k]
        tot = d["total"]
        cor = d["correct"]
        wr = d["wrong"]
        acc = 100.0 * cor / tot if tot else 0.0
        print(f"{k}: correct={cor} wrong={wr} total={tot} acc={acc:.1f}%")

    print()
    print("=== Per offence bucket (keyword heuristic from paragraph) ===")
    for k in sorted(by_bucket.keys(), key=lambda x: -by_bucket[x]["total"]):
        d = by_bucket[k]
        tot = d["total"]
        cor = d["correct"]
        wr = d["wrong"]
        acc = 100.0 * cor / tot if tot else 0.0
        print(f"{k}: correct={cor} wrong={wr} total={tot} acc={acc:.1f}%")

    print()
    print("=== When truth = Partly_Allowed — predicted distribution ===")
    sub = [r for r in rows if r.get("counted_for_accuracy") == "True" and r["truth"] == "Partly_Allowed"]
    for pred, n in Counter((r.get("predicted") or "") for r in sub).most_common():
        print(f"  predicted {pred}: {n}")


if __name__ == "__main__":
    main()
