"""
Improved Feature Engineering for Appeal Outcome Prediction.

Canonical input = combined_text (same as a single user paragraph at inference).
TF-IDF + SelectKBest are fit ONLY on the training split (no label leakage).
"""

from __future__ import annotations

import importlib.util
import json
import pickle
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.preprocessing import LabelEncoder, StandardScaler

COMP3_DIR = Path(__file__).resolve().parent


def _load_paragraph_features():
    """Load without importing `src` package (avoids eager torch import)."""
    path = COMP3_DIR / "src" / "core" / "appeal_paragraph_features.py"
    spec = importlib.util.spec_from_file_location("appeal_paragraph_features", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_paragraph_mod = _load_paragraph_features()
extract_unified_legal_features_dataframe = _paragraph_mod.extract_unified_legal_features_dataframe

LEAKAGE_FORBIDDEN_COLUMNS = [
    "court_of_appeal_analysis_summary",
    "coa_final_outcome_class",
    "coa_conviction_status",
    "coa_sentence_type",
    "release_ordered",
    "final_charge_after_appeal",
    "combined_outcome",
    "conviction_clean",
]

PRE_APPEAL_TEXT_COLUMNS = [
    "brief_facts_summary",
    "grounds_of_appeal_raw_text_summary",
    "hc_judgment_summary",
    "defence_version_summary",
    "witness_evidence_analysis_summary",
]


def hybrid_feature_selection(X_train: pd.DataFrame, y_train: np.ndarray) -> list:
    """Select BERT + TF-IDF columns using training data only; keep all legal columns."""
    print("Implementing hybrid feature selection (train-only k-best)...")

    all_features = X_train.columns.tolist()
    legal_features = []
    bert_features = []
    tfidf_features = []

    for feature in all_features:
        if feature.startswith("bert_"):
            bert_features.append(feature)
        elif feature.startswith("tfidf_"):
            tfidf_features.append(feature)
        else:
            legal_features.append(feature)

    print(f"Feature inventory (train):")
    print(f"  Legal features: {len(legal_features)}")
    print(f"  BERT embeddings: {len(bert_features)}")
    print(f"  TF-IDF features: {len(tfidf_features)}")

    selected_features = legal_features.copy()
    print(f"Keeping all {len(legal_features)} legal features")

    if bert_features:
        n_bert = min(100, len(bert_features))
        print(f"Selecting top {n_bert} BERT features (train only)...")
        X_bert = X_train[bert_features]
        selector_bert = SelectKBest(score_func=f_classif, k=n_bert)
        selector_bert.fit(X_bert, y_train)
        selected_bert_mask = selector_bert.get_support()
        selected_bert = [bert_features[i] for i, sel in enumerate(selected_bert_mask) if sel]
        selected_features.extend(selected_bert)
        print(f"Selected {len(selected_bert)} BERT features")

    if tfidf_features:
        n_tfidf = min(50, len(tfidf_features))
        print(f"Selecting top {n_tfidf} TF-IDF features (train only)...")
        X_tfidf = X_train[tfidf_features]
        selector_tfidf = SelectKBest(score_func=f_classif, k=n_tfidf)
        selector_tfidf.fit(X_tfidf, y_train)
        selected_tfidf_mask = selector_tfidf.get_support()
        selected_tfidf = [tfidf_features[i] for i, sel in enumerate(selected_tfidf_mask) if sel]
        selected_features.extend(selected_tfidf)
        print(f"Selected {len(selected_tfidf)} TF-IDF features")

    print(f"Total selected features: {len(selected_features)}")
    return selected_features


def improved_feature_engineering():
    print("=" * 70)
    print("IMPROVED FEATURE ENGINEERING (paragraph-aligned, leakage-safe)")
    print("=" * 70)
    print()

    print("Loading cleaned dataset...")
    df = pd.read_csv(COMP3_DIR / "dataset_cleaned_v2.csv")
    print(f"Loaded: {len(df)} records")

    present_forbidden = [c for c in LEAKAGE_FORBIDDEN_COLUMNS if c in df.columns]
    if present_forbidden:
        print("Leakage guard: excluding post-judgment/proxy columns from inputs")
        print(f"Excluded columns: {present_forbidden}")
        df = df.drop(columns=present_forbidden)

    text_columns = [col for col in PRE_APPEAL_TEXT_COLUMNS if col in df.columns]
    if not text_columns:
        raise ValueError("No valid pre-appeal text columns found for feature engineering.")
    df["combined_text"] = df[text_columns].fillna("").agg(" ".join, axis=1)

    df = df[df["combined_text"].str.len() > 10].copy()
    print(f"Records after filtering empty text: {len(df)}")

    df = df.dropna(subset=["outcome_clean"])
    all_features = extract_unified_legal_features_dataframe(df)
    print(f"Unified paragraph-based legal features: {all_features.shape[1]} columns")

    y = df["outcome_clean"].values
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print(f"Target classes: {list(label_encoder.classes_)}")
    print(f"Class distribution: {np.bincount(y_encoded)}")
    print()

    # --- Temporal / grouped split (before TF-IDF) ---
    print("Step: Grouped Temporal Train/Test Split")
    print("-" * 50)

    if "coa_year" not in df.columns:
        raise ValueError("coa_year is required for temporal split.")

    case_col = "court_of_appeal_case_no" if "court_of_appeal_case_no" in df.columns else None
    years = pd.to_numeric(df["coa_year"], errors="coerce")
    years = years.fillna(years.median() if years.notna().any() else 0)

    split_meta: dict = {}
    if case_col:
        case_year_df = pd.DataFrame(
            {
                "case_id": df[case_col].fillna("unknown_case"),
                "coa_year": years,
            }
        )
        case_year_summary = case_year_df.groupby("case_id", as_index=False)["coa_year"].max()
        cutoff_year = float(np.quantile(case_year_summary["coa_year"].values, 0.8))

        train_cases = set(case_year_summary[case_year_summary["coa_year"] < cutoff_year]["case_id"])
        test_cases = set(case_year_summary[case_year_summary["coa_year"] >= cutoff_year]["case_id"])

        if not train_cases or not test_cases:
            case_year_summary = case_year_summary.sort_values(["coa_year", "case_id"]).reset_index(drop=True)
            split_case_idx = int(len(case_year_summary) * 0.8)
            train_cases = set(case_year_summary.iloc[:split_case_idx]["case_id"])
            test_cases = set(case_year_summary.iloc[split_case_idx:]["case_id"])
            cutoff_year = float(case_year_summary.iloc[split_case_idx]["coa_year"]) if split_case_idx < len(case_year_summary) else float(case_year_summary["coa_year"].max())

        train_mask = case_year_df["case_id"].isin(train_cases).values
        test_mask = case_year_df["case_id"].isin(test_cases).values
        split_meta["split_strategy"] = "grouped_temporal_by_case"
        split_meta["temporal_cutoff_year"] = cutoff_year
        split_meta["n_train_cases"] = len(train_cases)
        split_meta["n_test_cases"] = len(test_cases)
    else:
        df_sorted = df.assign(_coa_year_num=years).sort_values("_coa_year_num")
        split_idx = int(len(df_sorted) * 0.8)
        train_idx = df_sorted.iloc[:split_idx].index
        test_idx = df_sorted.iloc[split_idx:].index
        train_mask = df.index.isin(train_idx)
        test_mask = df.index.isin(test_idx)
        split_meta["split_strategy"] = "temporal_row_split_fallback"

    if len(np.unique(y_encoded[train_mask])) < len(label_encoder.classes_) or len(np.unique(y_encoded[test_mask])) < 2:
        raise ValueError("Temporal/grouped split produced insufficient class coverage.")

    # --- TF-IDF: fit train only ---
    print("Step: TF-IDF (fit on train split only)")
    print("-" * 50)

    tfidf_vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=1,
        max_df=0.95,
        ngram_range=(1, 2),
        stop_words="english",
        lowercase=True,
        strip_accents="ascii",
    )

    train_text = df.loc[df.index[train_mask], "combined_text"]
    tfidf_vectorizer.fit(train_text)
    tfidf_matrix = tfidf_vectorizer.transform(df["combined_text"])
    tfidf_features = tfidf_vectorizer.get_feature_names_out()

    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=[f"tfidf_{f}" for f in tfidf_features],
        index=df.index,
    )
    print(f"TF-IDF features: {len(tfidf_features)} (vectorizer fit on {train_mask.sum()} train rows)")

    with open(COMP3_DIR / "improved_tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(tfidf_vectorizer, f)

    # Combine legal + TF-IDF
    all_X = pd.concat([all_features, tfidf_df], axis=1)
    print(f"Total features before BERT: {len(all_X.columns)}")

    # BERT
    bert_path = COMP3_DIR / "bert_embeddings_all.npy"
    try:
        bert_embeddings = np.load(bert_path)
        if len(bert_embeddings) == len(df):
            bert_df = pd.DataFrame(
                bert_embeddings,
                columns=[f"bert_{i}" for i in range(bert_embeddings.shape[1])],
                index=df.index,
            )
            all_X = pd.concat([all_X, bert_df], axis=1)
            print(f"Added {bert_embeddings.shape[1]} BERT features")
        else:
            print(f"BERT shape {bert_embeddings.shape} != df {len(df)} — skipping BERT")
    except FileNotFoundError:
        print("bert_embeddings_all.npy not found — skipping BERT")

    print(f"Final feature count: {len(all_X.columns)}")

    # Feature selection (train only)
    print("Step: Hybrid feature selection")
    print("-" * 50)

    X_train_raw = all_X.loc[df.index[train_mask]]
    y_train_split = y_encoded[train_mask]

    selected_features = hybrid_feature_selection(X_train_raw, y_train_split)

    bert_count = sum(1 for f in selected_features if f.startswith("bert_"))
    tfidf_count = sum(1 for f in selected_features if f.startswith("tfidf_"))
    legal_count = len(selected_features) - bert_count - tfidf_count

    X_train = all_X.loc[df.index[train_mask]]
    X_test = all_X.loc[df.index[test_mask]]
    y_train = y_encoded[train_mask]
    y_test = y_encoded[test_mask]

    train_years = years[train_mask]
    test_years = years[test_mask]

    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    print(f"Years in train: {train_years.min()}-{train_years.max()}")
    print(f"Years in test: {test_years.min()}-{test_years.max()}")
    print()

    X_train_selected = X_train[selected_features]
    X_test_selected = X_test[selected_features]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_selected)
    X_test_scaled = scaler.transform(X_test_selected)

    X_train_final = pd.DataFrame(X_train_scaled, columns=selected_features)
    X_test_final = pd.DataFrame(X_test_scaled, columns=selected_features)

    X_train_final.to_csv(COMP3_DIR / "X_train_improved.csv", index=False)
    X_test_final.to_csv(COMP3_DIR / "X_test_improved.csv", index=False)

    np.save(COMP3_DIR / "y_train_improved.npy", y_train)
    np.save(COMP3_DIR / "y_test_improved.npy", y_test)

    with open(COMP3_DIR / "improved_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(COMP3_DIR / "improved_label_encoder.pkl", "wb") as f:
        pickle.dump(label_encoder, f)
    with open(COMP3_DIR / "improved_selected_features.pkl", "wb") as f:
        pickle.dump(selected_features, f)

    metadata = {
        "pipeline": "paragraph_aligned_combined_text",
        "tfidf_fit_scope": "train_split_only",
        "feature_selection_scope": "train_split_only",
        "excluded_inference_unavailable": ["coa_year", "appeal_duration_days"],
        "total_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "total_features_raw": len(all_X.columns),
        "selected_features": len(selected_features),
        "feature_composition": {
            "legal": legal_count,
            "bert": bert_count,
            "tfidf": tfidf_count,
        },
        "target_classes": list(label_encoder.classes_),
        **split_meta,
        "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(COMP3_DIR / "improved_feature_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

    print("✅ All files saved successfully!")
    print("=" * 70)
    print(f"Selected {len(selected_features)} features (legal={legal_count}, bert={bert_count}, tfidf={tfidf_count})")
    return X_train_final, X_test_final, y_train, y_test, selected_features, label_encoder


if __name__ == "__main__":
    improved_feature_engineering()
