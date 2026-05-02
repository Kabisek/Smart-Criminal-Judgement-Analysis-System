"""
Canonical labels for Component 3 analytics dashboard.
Normalizes high court names and coarse regions from free-text location_of_offence.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from comp3.region_gazetteer import sorted_region_patterns, region_pattern_match

# Region buckets when offence location cannot be mapped to a gazetteer region
REGION_LOCATION_NOT_STATED = "Location not stated"
REGION_LOCATION_NOT_MAPPED = "Location not mapped"

# Known high court spellings / variants -> single display label (Title style)
HIGH_COURT_CANON: Dict[str, str] = {
    "amuradhapura": "Anuradhapura",
    "anuradhapura": "Anuradhapura",
    "awissawella": "Avissawella",
    "avissawella": "Avissawella",
    "moneragala": "Monaragala",
    "monaragala": "Monaragala",
    "nuwaraeliya": "Nuwara Eliya",
    "nuwara eliya": "Nuwara Eliya",
    "nuwara-eliya": "Nuwara Eliya",
    "batticaloa": "Batticaloa",
    "baticaloa": "Batticaloa",
    "chilaw": "Chilaw",
    "chillaw": "Chilaw",
    "chilaw ": "Chilaw",
    "gampaha": "Gampaha",
    "gampaha ": "Gampaha",
    "hambantota": "Hambantota",
    "hambanthota": "Hambantota",
    "jaffna": "Jaffna",
    "kandy": "Kandy",
    "kalmunai": "Kalmunai",
    "kalutara": "Kalutara",
    "kaluthara": "Kalutara",
    "katutara": "Kalutara",
    "kegalle": "Kegalle",
    "kurunegala": "Kurunegala",
    "kurunagala": "Kurunegala",
    "kurunakala": "Kurunegala",
    "matara": "Matara",
    "matale": "Matale",
    "matable": "Matale",
    "negombo": "Negombo",
    "panadura": "Panadura",
    "puttalam": "Puttalam",
    "ratnapura": "Ratnapura",
    "rathnapura": "Ratnapura",
    "trincomalee": "Trincomalee",
    "vavuniya": "Vavuniya",
    "vavunia": "Vavuniya",
    "vauniya": "Vavuniya",
    "badulla": "Badulla",
    "colombo": "Colombo",
    "galle": "Galle",
    "ampara": "Ampara",
    "polonnaruwa": "Polonnaruwa",
    "mannar": "Mannar",
    "kilinochchi": "Kilinochchi",
    "homagama": "Homagama",
    "balapitiya": "Balapitiya",
    "embilipitiya": "Embilipitiya",
    "kuliyapitiya": "Kuliyapitiya",
    "tangalle": "Tangalle",
    "warakapola": "Warakapola",
    "unknown": "Unknown",
}

# Gazetteer loaded from region_gazetteer (longer patterns first).
_REGION_PATTERNS: List[Tuple[str, str]] = sorted_region_patterns()


def _collapse_ws_hyphen(s: str) -> str:
    """Lowercase, normalize spaces/hyphens; keep commas for court-name parsing."""
    s = s.lower().strip()
    s = re.sub(r"[\s\-_;]+", " ", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    return s.strip()


def _extract_high_court_place(key: str) -> str:
    """
    Reduce long formal names (Provincial High Court … holden in X) to the place token.
    `key` must already be _collapse_ws_hyphen form.
    """
    k = key.strip()
    if not k:
        return ""
    for _ in range(10):
        prev = k
        m = re.search(r"\bholden in (.+)$", k)
        if m:
            k = _collapse_ws_hyphen(m.group(1))
            continue
        m = re.search(r"\bheld in (.+)$", k)
        if m:
            k = _collapse_ws_hyphen(m.group(1))
            continue
        if "," in k:
            k = _collapse_ws_hyphen(k.split(",")[-1])
            continue
        m = re.search(r"\bhigh court of (.+)$", k)
        if m:
            k = _collapse_ws_hyphen(m.group(1))
            continue
        m = re.search(r"\bprovincial high court of (.+)$", k)
        if m:
            k = _collapse_ws_hyphen(m.group(1))
            continue
        m = re.search(r"^provincial high court (.+)$", k)
        if m and not m.group(1).lower().lstrip().startswith("of "):
            k = _collapse_ws_hyphen(m.group(1))
            continue
        if prev == k:
            break
    k = re.sub(r"^the\s+", "", k)
    k = re.sub(
        r"^(western|central|north western|northwestern|southern|sabaragamuwa|uva|"
        r"north central|northern|eastern)\s+province\s*",
        "",
        k,
    )
    k = k.strip()
    if not k:
        return ""
    if re.fullmatch(r"(western|central|north western|northwestern|southern|sabaragamuwa|uva|"
                    r"north central|northern|eastern)(\s+province)?", k):
        return ""
    return k


def canonicalize_high_court(raw) -> str:
    if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
        return "Unknown"
    s = str(raw).strip()
    if not s or s.lower() == "nan":
        return "Unknown"
    key = _collapse_ws_hyphen(s)
    if key in HIGH_COURT_CANON:
        return HIGH_COURT_CANON[key]

    short = _extract_high_court_place(key)
    if short and short != key:
        if short in HIGH_COURT_CANON:
            return HIGH_COURT_CANON[short]
        key = short

    if key in HIGH_COURT_CANON:
        return HIGH_COURT_CANON[key]

    if not key:
        return "Unknown"
    return " ".join(w.capitalize() for w in key.split())


def infer_region_bucket(location_text) -> str:
    """
    Map free-text location_of_offence to a coarse region for dashboard analytics.
    Returns REGION_LOCATION_NOT_STATED when the field is empty/NaN.
    Returns REGION_LOCATION_NOT_MAPPED when text exists but no gazetteer keyword matched.
    """
    if location_text is None or (isinstance(location_text, float) and str(location_text) == "nan"):
        return REGION_LOCATION_NOT_STATED
    s = str(location_text).strip()
    if not s or s.lower() == "nan":
        return REGION_LOCATION_NOT_STATED
    norm = _collapse_ws_hyphen(s)
    norm_compact = re.sub(r"\s+", "", norm)
    for pattern, label in _REGION_PATTERNS:
        if region_pattern_match(norm, norm_compact, pattern):
            return label
    return REGION_LOCATION_NOT_MAPPED


def offence_group_column(df) -> str:
    """Return column name to use for grouped offence analytics."""
    if "offence_category_grouped" in df.columns:
        return "offence_category_grouped"
    return "offence_category"
