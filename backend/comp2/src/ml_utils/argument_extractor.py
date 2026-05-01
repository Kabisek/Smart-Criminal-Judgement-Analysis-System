"""
Argument Pattern Extraction Module
Extracts argument patterns from similar cases.
Uses KNN (trained model, cosine similarity) when available; falls back to ChromaDB search.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def _build_case_info_from_chroma(chroma_id: str, meta: Dict, document: str) -> Dict:
    """Build case_info from ChromaDB search result."""
    case_id = meta.get("case_id", chroma_id) if meta else chroma_id
    return {
        "case_id": str(case_id),
        "cleaned_text": document or "",
        "full_text": document or "",
        "judge_names": meta.get("judge_names", "") if meta else "",
        "judge_statement": meta.get("judge_statement", "") if meta else "",
        "year": meta.get("year", "Unknown") if meta else "Unknown",
        "source": meta.get("source", "") if meta else "",
        "file_path": meta.get("file_path", "") if meta else "",
    }


class ArgumentExtractor:
    """Extract argument patterns from similar cases. Uses KNN when available, else ChromaDB."""

    def __init__(
        self,
        chroma_persist_dir: str = None,
        collection_name: str = "legal_cases",
    ):
        """
        Initialize argument extractor with ChromaDB and optional KNN retriever.

        Args:
            chroma_persist_dir: Path to ChromaDB (default: from config)
            collection_name: ChromaDB collection name
        """
        self.chroma_store = None
        self.knn_retriever = None
        self._init_chroma(chroma_persist_dir, collection_name)
        self._init_knn()

    def _init_chroma(self, chroma_persist_dir: str, collection_name: str):
        """Initialize ChromaDB store. Gracefully degrades if ChromaDB is corrupted."""
        try:
            from comp2.src.retrieval.chroma_store import ChromaStore
            from comp2.api.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

            persist_dir = chroma_persist_dir or str(CHROMA_PERSIST_DIR)
            coll_name = collection_name or CHROMA_COLLECTION_NAME

            if not Path(persist_dir).exists():
                logger.warning(f"ChromaDB path not found: {persist_dir}")
                return

            self.chroma_store = ChromaStore(
                persist_directory=persist_dir,
                collection_name=coll_name,
            )
            if self.chroma_store.count() > 0:
                logger.info(f"ArgumentExtractor: ChromaDB loaded ({self.chroma_store.count()} vectors)")
            else:
                self.chroma_store = None
        except BaseException as e:
            err = str(e)
            if "range start index" in err or "PanicException" in err:
                logger.warning("ArgumentExtractor: ChromaDB CORRUPTED. Delete chroma_db_comp2 and re-populate.")
            else:
                logger.warning(f"ArgumentExtractor: ChromaDB not available: {e}")
            self.chroma_store = None

    def _init_knn(self) -> None:
        """Initialize KNN retriever for pattern extraction (trained model, cosine similarity)."""
        try:
            from comp2.src.ml_utils.knn_retriever import KNNRetriever
            self.knn_retriever = KNNRetriever(chroma_store=self.chroma_store)
            if self.knn_retriever.is_available():
                logger.info("ArgumentExtractor: KNN retriever enabled (trained model)")
            else:
                self.knn_retriever = None
        except Exception as e:
            logger.warning(f"ArgumentExtractor: KNN not available: {e}")
            self.knn_retriever = None

    def extract_argument_patterns(
        self,
        query_embedding,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Extract argument patterns from similar cases.
        Uses KNN (trained model, cosine similarity) when available; else ChromaDB search.

        Args:
            query_embedding: Embedding vector of the new case
            top_k: Number of similar cases to analyze

        Returns:
            List of argument patterns from similar cases
        """
        if self.chroma_store is None:
            logger.warning("ChromaDB not available; returning empty argument patterns")
            return []

        ids = []
        distances = []
        metadatas = []
        documents = []

        if self.knn_retriever and self.knn_retriever.is_available():
            chroma_ids, dists = self.knn_retriever.find_similar(query_embedding, top_k=top_k)
            if chroma_ids:
                metadatas, documents = self.chroma_store.get_by_ids(chroma_ids)
                ids = chroma_ids
                distances = dists
                logger.info(f"Argument patterns from KNN (cosine similarity): {len(ids)} cases")
        else:
            ids, distances, metadatas, documents = self.chroma_store.search(
                query_embedding, n_results=top_k
            )

        if not ids:
            return []

        argument_patterns = []
        for i, cid in enumerate(ids):
            distance = distances[i] if i < len(distances) else 0.0
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = documents[i] if documents and i < len(documents) else ""
            case_info = _build_case_info_from_chroma(cid, meta, doc)
            patterns = self._extract_patterns_from_case(case_info, float(distance))
            if patterns:
                argument_patterns.extend(patterns)

        return argument_patterns

    def _extract_patterns_from_case(self, case_info: Dict, distance: float) -> List[Dict]:
        """Extract argument patterns from a single case."""
        patterns = []
        if not case_info:
            return patterns

        case_text = case_info.get("cleaned_text", case_info.get("full_text", ""))
        if not case_text or len(case_text) < 100:
            return patterns

        judge_info = self._get_judge_info(case_info)
        legal_principles = self._extract_legal_principles(case_text)
        argument_points = self._extract_argument_points(case_text)
        perspective = self._determine_perspective(case_text)

        pattern = {
            "case_id": case_info.get("case_id", "Unknown"),
            "year": case_info.get("year", "Unknown"),
            "similarity_score": float(1 - distance),
            "perspective": perspective,
            "judge_names": judge_info.get("judge_names", []),
            "judge_statements": judge_info.get("key_statements", []),
            "legal_principles": legal_principles,
            "argument_points": argument_points,
            "case_excerpt": case_text[:500],
        }
        patterns.append(pattern)
        return patterns

    def _get_judge_info(self, case_info: Dict) -> Dict:
        """Extract judge information from case (supports ChromaDB metadata)."""
        judge_info = {"judge_names": [], "key_statements": []}

        # Try judge_info_json first
        judge_info_json = case_info.get("judge_info_json", "{}")
        if judge_info_json and isinstance(judge_info_json, str):
            try:
                judge_data = json.loads(judge_info_json)
                judge_info["judge_names"] = judge_data.get("judge_names", [])
                holdings = judge_data.get("judge_holdings", [])
                statements = judge_data.get("judge_statements", [])
                all_statements = []
                for holding in holdings[:2]:
                    all_statements.append({
                        "judge": holding.get("judge_name", "Court"),
                        "statement": holding.get("holding", "")[:200],
                    })
                for stmt in statements[:2]:
                    all_statements.append({
                        "judge": stmt.get("judge_name", "Unknown"),
                        "statement": stmt.get("statement", "")[:200],
                    })
                judge_info["key_statements"] = all_statements[:3]
            except json.JSONDecodeError:
                pass

        # Fallback: judge_names from metadata (string, e.g. "Judge A | Judge B")
        if not judge_info["judge_names"]:
            judge_names_str = case_info.get("judge_names", case_info.get("judges", ""))
            if judge_names_str:
                judge_info["judge_names"] = [
                    n.strip()
                    for n in str(judge_names_str).replace("|", ",").split(",")
                    if n.strip()
                ]

        # Use judge_statement column (ChromaDB metadata) when available
        judge_statement = case_info.get("judge_statement", case_info.get("judge_statements_and_judgments", ""))
        if judge_statement and not judge_info["key_statements"]:
            for part in str(judge_statement).split("|")[:5]:
                part = part.strip()
                if part and len(part) > 30:
                    judge_info["key_statements"].append({"judge": "Court", "statement": part[:200]})

        return judge_info

    def _extract_legal_principles(self, text: str) -> List[str]:
        """Extract legal principles, sections, and statutes mentioned."""
        principles = []
        section_pattern = r'(?:Section|S\.|Sections|Ss\.)\s+(\d+(?:\([a-z0-9]+\))?(?:\s+(?:and|&)\s+\d+(?:\([a-z0-9]+\))?)?(?:\s+of\s+(?:the\s+)?[A-Z][^,\.;\n]+)?)'
        sections = re.findall(section_pattern, text, re.IGNORECASE)
        principles.extend([f"Section {s}" if not s.lower().startswith("section") else s for s in sections[:8]])

        act_pattern = r'(?:[A-Z][a-z]+\s+)*Act(?:\s+No\.?\s*\d+\s+of\s+\d{4})?|Penal\s+Code|Evidence\s+Ordinance|Criminal\s+Procedure\s+Code'
        acts = re.findall(act_pattern, text, re.IGNORECASE)
        principles.extend(acts[:5])

        principle_patterns = [
            r"(?:principle|doctrine|rule)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:established|well-established)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+principle",
            r"(?:right\s+of\s+private\s+defence|burden\s+of\s+proof|reasonable\s+doubt|preponderance\s+of\s+evidence)",
        ]
        for pattern in principle_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, str):
                    principles.append(m.strip())

        cleaned = []
        seen = set()
        for p in principles:
            p_clean = re.sub(r"\s+", " ", p).strip()
            if p_clean.lower() not in seen and len(p_clean) > 3:
                cleaned.append(p_clean)
                seen.add(p_clean.lower())
        return cleaned[:10]

    def _extract_argument_points(self, text: str) -> List[str]:
        """Extract key argument points from case text."""
        argument_points = []
        argument_indicators = [
            r"(?:The\s+prosecution|Prosecution|State|Complainant|Respondent|The\s+defense|Defense|Defence|Accused|Appellant|Court|Judge|Magistrate)\s+(?:argues?|contends?|submits?|stated|submitted|contended|observed|held|decided|ruled|concluded)[\s:]+(.+?)(?:\.|;|\n)",
            r"(?:The\s+learned\s+)?Counsel\s+(?:for\s+the\s+)?(?:appellant|respondent|prosecution|defense|accused)\s+(?:argued|submitted|stated|contended)[\s:]+(.+?)(?:\.|;|\n)",
            r"(?:It\s+is\s+|It\s+was\s+)(?:argued|contended|submitted|alleged|observed|held|found)\s+that\s+(.+?)(?:\.|;|\n)",
            r"(?:The\s+main\s+ground\s+of\s+appeal|The\s+victim\s+had\s+said|The\s+accused\s+had\s+said)[\s:]+(.+?)(?:\.|;|\n)",
        ]
        seen_points = set()
        for pattern in argument_indicators:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                point = re.sub(r"\s+", " ", match.group(1).strip())
                if 25 < len(point) < 400 and point.lower() not in seen_points:
                    argument_points.append(point)
                    seen_points.add(point.lower())
        argument_points.sort(key=len, reverse=True)
        return argument_points[:6]

    def _determine_perspective(self, text: str) -> str:
        """Determine prosecution/defense perspective."""
        text_lower = text.lower()
        prosecution_keywords = ["convicted", "guilty", "prosecution proved", "evidence establishes", "beyond reasonable doubt", "offence committed", "accused found guilty"]
        defense_keywords = ["acquitted", "not guilty", "defense succeeds", "reasonable doubt", "evidence insufficient", "prosecution failed", "accused acquitted"]
        p_score = sum(1 for k in prosecution_keywords if k in text_lower)
        d_score = sum(1 for k in defense_keywords if k in text_lower)
        if p_score > d_score:
            return "prosecution"
        if d_score > p_score:
            return "defense"
        return "neutral"

    def format_patterns_for_llm(self, patterns: List[Dict]) -> str:
        """Format argument patterns for LLM context."""
        if not patterns:
            return ""
        formatted = "\n[MODEL-EXTRACTED ARGUMENT PATTERNS FROM SIMILAR CASES]:\n"
        for i, pattern in enumerate(patterns[:5], 1):
            formatted += f"\n[PATTERN {i}]:\n"
            formatted += f"Case: {pattern.get('case_id', 'Unknown')} ({pattern.get('year', 'Unknown')})\n"
            formatted += f"Similarity: {pattern.get('similarity_score', 0):.2f}\n"
            formatted += f"Perspective: {pattern.get('perspective', 'neutral')}\n"
            if pattern.get("judge_names"):
                formatted += f"Judges: {', '.join(pattern['judge_names'])}\n"
            if pattern.get("judge_statements"):
                formatted += "Key Judge Statements:\n"
                for stmt in pattern["judge_statements"][:2]:
                    formatted += f"  - {stmt.get('judge', 'Court')}: {stmt.get('statement', '')[:150]}...\n"
            if pattern.get("legal_principles"):
                formatted += f"Legal Principles: {', '.join(pattern['legal_principles'][:3])}\n"
            if pattern.get("argument_points"):
                for point in pattern["argument_points"][:2]:
                    formatted += f"  - {point[:150]}...\n"
        return formatted
