"""
Unified appeal features from a single canonical paragraph (= training combined_text).

Training and inference MUST use this module so TF-IDF/BERT/legal rows align.
Temporal columns (coa_year, appeal_duration_days) are excluded — not available at prediction time.
"""

from __future__ import annotations

from typing import Dict, List, Sequence

import pandas as pd

PRE_APPEAL_SLOT_NAMES = [
    "brief_facts_summary",
    "grounds_of_appeal_raw_text_summary",
    "hc_judgment_summary",
    "defence_version_summary",
    "witness_evidence_analysis_summary",
]

OFFENCE_CATEGORIES: List[str] = [
    "Drug_Related",
    "Murder_Related",
    "Sexual_Offenses",
    "Other",
    "Fraud_Corruption",
    "Robbery_Theft",
    "Assault_Violence",
    "Environmental",
    "Firearms_Weapons",
    "Traffic_Vehicle",
    "Customs",
]

APPEAL_TYPES: List[str] = [
    "Sentence_Only",
    "Both",
    "Revision",
    "Conviction_Only",
    "Other",
    "Writ",
]

GROUND_KEYWORDS: Dict[str, List[str]] = {
    "contradictions": ["contradiction", "inconsistent", "conflicting", "discrepancy"],
    "chain_of_custody": ["chain of custody", "custody", "preservation", "handling"],
    "illegal_search": ["illegal search", "unlawful search", "search raid", "illegal raid"],
    "wrong_identification": ["identification", "identify", "mistaken identity", "id parade"],
    "dying_declaration": ["dying declaration", "deathbed statement"],
    "circumstantial": ["circumstantial", "indirect evidence", "circumstantial evidence"],
    "medical_inconsistency": ["medical", "jmo", "post-mortem", "autopsy", "medical evidence"],
    "misdirection": ["misdirection", "wrong direction", "legal error", "direction"],
    "procedural_error": ["procedural", "procedure", "process error", "procedural defect"],
    "new_evidence": ["new evidence", "fresh evidence", "additional evidence"],
    "excessive_sentence": ["excessive", "harsh", "inadequate sentence", "sentence"],
    "delay_prejudice": ["delay", "prejudice", "lapse of time"],
    "judicial_bias": ["bias", "unfair", "prejudiced judge"],
}

EVIDENCE_KEYWORDS: Dict[str, List[str]] = {
    "eyewitness": ["eyewitness", "witness", "testimony", "eye witness"],
    "child_witness": ["child witness", "minor witness", "child testimony"],
    "expert_evidence": ["expert", "jmo", "analyst", "specialist", "expert testimony"],
    "forensic_evidence": ["forensic", "dna", "fingerprint", "ballistic", "forensic evidence"],
    "dying_declaration": ["dying declaration"],
    "confession": ["confession", "admitted", "dock statement", "confessed"],
    "procedural_defects": ["procedural defect", "process error", "procedural"],
    "digital_evidence": ["cctv", "phone", "digital", "video", "recording", "digital evidence"],
    "hospital_treatment": ["hospital", "medical treatment", "admitted to hospital"],
}

MEDICAL_TERMS = ["medical", "jmo", "post-mortem", "autopsy", "pathologist", "medical evidence"]


def infer_offence_category(text: str) -> str:
    """Single label from paragraph (priority order)."""
    t = text.lower()
    if any(k in t for k in ["heroin", "cannabis", "dangerous drugs", "poisons, opium", "drug trafficking", "opium", "narcotic", "54a", "diacetylmorphine"]):
        return "Drug_Related"
    if any(k in t for k in ["murder", "section 296", "homicide", "culpable homicide", "death sentence"]):
        return "Murder_Related"
    if any(k in t for k in ["rape", "sexual", "365b", "365 b", "364(", "grave sexual", "sexual abuse"]):
        return "Sexual_Offenses"
    if any(k in t for k in ["bribery", "corruption", "fraud", "cheating", "embezzlement", "386"]):
        return "Fraud_Corruption"
    if any(k in t for k in ["robbery", "theft", "burglary", "section 380", "section 394"]):
        return "Robbery_Theft"
    if any(k in t for k in ["assault", "hurt", "grievous", "section 314", "317"]):
        return "Assault_Violence"
    if any(k in t for k in ["environment", "wildlife", "forest"]):
        return "Environmental"
    if any(k in t for k in ["firearm", "weapon", "explosives"]):
        return "Firearms_Weapons"
    if any(k in t for k in ["traffic", "motor traffic", "vehicle", "rash driving", "road traffic"]):
        return "Traffic_Vehicle"
    if any(k in t for k in ["customs", "import", "export"]):
        return "Customs"
    return "Other"


def infer_appeal_type(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["writ", "certiorari", "mandamus", "prohibition"]):
        return "Writ"
    if "revision" in t or ("review" in t and "appeal" not in t[:200]):
        return "Revision"
    if "sentence" in t and "conviction" in t:
        return "Both"
    if any(k in t for k in ["sentence only", "against sentence", "appeal against sentence"]):
        return "Sentence_Only"
    if any(k in t for k in ["conviction", "acquittal", "convicted"]):
        return "Conviction_Only"
    return "Other"


def _keyword_hits(text_lower: str, keywords: Sequence[str]) -> bool:
    return any(kw in text_lower for kw in keywords)


def extract_row_from_paragraph(text: str) -> Dict[str, float]:
    """All traditional legal columns derived only from one paragraph (same as combined_text)."""
    raw = text or ""
    t = raw.lower()
    char_len = float(len(raw))
    wc = float(len(raw.split()))

    out: Dict[str, float] = {}

    # Unified slots: training treats the paragraph as the concatenation of all sections.
    for slot in PRE_APPEAL_SLOT_NAMES:
        out[f"{slot}_length"] = char_len
        out[f"{slot}_word_count"] = wc

    for ground, keywords in GROUND_KEYWORDS.items():
        out[f"gnd_{ground}"] = float(_keyword_hits(t, keywords))

    for evidence, keywords in EVIDENCE_KEYWORDS.items():
        out[f"{evidence}_present"] = float(_keyword_hits(t, keywords))

    med_score = 0.0
    for term in MEDICAL_TERMS:
        if term in t:
            med_score += 1.0
    out["medical_evidence_score"] = med_score

    offence = infer_offence_category(raw)
    for cat in OFFENCE_CATEGORIES:
        out[f"offence_category_{cat}"] = float(offence == cat)

    appeal = infer_appeal_type(raw)
    for at in APPEAL_TYPES:
        out[f"appeal_type_{at}"] = float(appeal == at)

    # Interactions (match prior pipeline intent)
    murder = out.get("offence_category_Murder_Related", 0.0)
    drug = out.get("offence_category_Drug_Related", 0.0)
    eye = out.get("eyewitness_present", 0.0)
    forensic = out.get("forensic_evidence_present", 0.0)
    out["murder_with_eyewitness"] = murder * eye
    out["drug_with_forensic"] = drug * forensic

    ev_cols = [k for k in out if k.endswith("_present")]
    out["evidence_count"] = float(sum(out[k] for k in ev_cols))

    return out


def extract_unified_legal_features_dataframe(df: pd.DataFrame, text_col: str = "combined_text") -> pd.DataFrame:
    """Vectorized-friendly: apply paragraph features per row."""
    if text_col not in df.columns:
        raise ValueError(f"Missing {text_col}")
    rows = []
    for txt in df[text_col].fillna(""):
        rows.append(extract_row_from_paragraph(str(txt)))
    return pd.DataFrame(rows, index=df.index)


def traditional_feature_dict_for_columns(case_description: str, columns: Sequence[str]) -> Dict[str, float]:
    """Fill only the traditional (non-bert, non-tfidf) columns expected by the trained scaler."""
    base = extract_row_from_paragraph(case_description)
    out: Dict[str, float] = {}
    for col in columns:
        if col.startswith("bert_") or col.startswith("tfidf_"):
            continue
        out[col] = float(base.get(col, 0.0))
    return out


def get_expected_traditional_column_order() -> List[str]:
    """Stable column order for metadata (optional)."""
    sample = extract_row_from_paragraph("sample appeal appellant high court conviction sentence evidence witness section")
    return sorted(sample.keys())
