"""
Source Mapper — maps extracted case-analysis fields back to character offsets
in the original document text so the frontend can highlight the source passage.

Uses only Python stdlib (difflib) for fuzzy matching — no extra dependencies.
"""
import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.55


class SourceMapper:
    def __init__(self, full_text: str, pages: List[dict]):
        self.full_text = full_text
        self.full_text_lower = full_text.lower()
        self.pages = pages

    def _page_for_offset(self, char_offset: int) -> int:
        for p in reversed(self.pages):
            if char_offset >= p["char_offset"]:
                return p["page_num"]
        return 0

    def _exact_find(self, query: str) -> Optional[dict]:
        """Fast path: exact case-insensitive substring search."""
        idx = self.full_text_lower.find(query.lower())
        if idx == -1:
            return None
        return {
            "start_char": idx,
            "end_char": idx + len(query),
            "matched_text": self.full_text[idx : idx + len(query)],
            "page": self._page_for_offset(idx),
            "score": 1.0,
        }

    def _sliding_window_match(self, query: str, window_ratio: float = 1.4) -> Optional[dict]:
        """Slide a window across the text and return the best fuzzy match."""
        q_lower = query.lower().strip()
        q_len = len(q_lower)
        if q_len < 4:
            return None

        win_size = int(q_len * window_ratio)
        best_score = 0.0
        best_start = -1
        step = max(1, q_len // 4)

        for start in range(0, len(self.full_text_lower) - win_size + 1, step):
            window = self.full_text_lower[start : start + win_size]
            score = SequenceMatcher(None, q_lower, window).ratio()
            if score > best_score:
                best_score = score
                best_start = start

        if best_score < MATCH_THRESHOLD or best_start == -1:
            return None

        end = best_start + win_size
        return {
            "start_char": best_start,
            "end_char": end,
            "matched_text": self.full_text[best_start:end],
            "page": self._page_for_offset(best_start),
            "score": best_score,
        }

    def _find_best_span(self, value: str) -> Optional[dict]:
        """Try exact first, fall back to fuzzy sliding-window."""
        if not value or len(value.strip()) < 3:
            return None
        result = self._exact_find(value)
        if result:
            return result
        return self._sliding_window_match(value)

    def _find_sentence_span(self, long_text: str) -> Optional[dict]:
        """For multi-sentence fields, match the first sentence that exists in source."""
        sentences = re.split(r'[.!?]\s+', long_text.strip())
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            result = self._find_best_span(sent)
            if result:
                return result
        return self._find_best_span(long_text[:120])

    def map_fields(self, analyzed_case: dict) -> List[dict]:
        """
        Walk the analyzed_case_file structure and return a list of source spans.

        Each span: {field_id, page, start_char, end_char, matched_text}
        """
        case_file = analyzed_case.get("analyzed_case_file", analyzed_case)
        spans: List[dict] = []

        def _add(field_id: str, value: Any):
            if value is None:
                return
            if isinstance(value, list):
                for i, item in enumerate(value):
                    _add(f"{field_id}[{i}]", item)
                return
            if isinstance(value, dict):
                text = value.get("name") or value.get("text") or value.get("doubt_factor") or ""
                if not text:
                    return
                value = str(text)
            value = str(value).strip()
            if len(value) < 3:
                return
            if len(value) > 200:
                result = self._find_sentence_span(value)
            else:
                result = self._find_best_span(value)
            if result:
                spans.append({
                    "field_id": field_id,
                    "page": result["page"],
                    "start_char": result["start_char"],
                    "end_char": result["end_char"],
                    "matched_text": result["matched_text"],
                })

        header = case_file.get("case_header", {})
        _add("case_header.subject", header.get("subject"))

        timeline = case_file.get("incident_timeline", {})
        _add("incident_timeline.what_happened", timeline.get("what_happened"))
        _add("incident_timeline.where_it_happened", timeline.get("where_it_happened"))
        for i, d in enumerate(timeline.get("key_dates", [])):
            _add(f"incident_timeline.key_dates[{i}]", d)

        parties = case_file.get("parties_and_roles", {})
        _add("parties_and_roles.accused", parties.get("accused"))
        _add("parties_and_roles.complainant", parties.get("complainant"))
        for i, w in enumerate(parties.get("doubters_witnesses", [])):
            _add(f"parties_and_roles.witnesses[{i}]", w)

        synthesis = case_file.get("argument_synthesis", {})
        for i, p in enumerate(synthesis.get("prosecution_logic", [])):
            _add(f"argument_synthesis.prosecution[{i}]", p)
        for i, d in enumerate(synthesis.get("defense_logic", [])):
            _add(f"argument_synthesis.defense[{i}]", d)
        for i, r in enumerate(synthesis.get("reasonable_doubt_factors", [])):
            _add(f"argument_synthesis.doubt[{i}]", r)

        _add("final_judicial_opinion", case_file.get("final_judicial_opinion"))

        logger.info(f"Source mapper: matched {len(spans)} of fields to document text")
        return spans
