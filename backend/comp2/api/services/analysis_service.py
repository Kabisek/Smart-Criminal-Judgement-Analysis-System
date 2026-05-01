"""
Analysis Service - Component 2
ChromaDB-only retrieval. Builds case_info from ChromaDB search results.
No feature_vectors.pkl, merged_v2.csv, or NN model at runtime.
"""
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from comp2.src.document_processing.processor import MultiFormatProcessor
from comp2.src.ml_utils.feature_extractor import FeatureExtractor
from comp2.src.ml_utils.text_cleaner import TextCleaner
from comp2.src.ml_utils.cluster_predictor import ClusterPredictor
from comp2.src.llm.client import LLMClient
from comp2.src.reasoning.enhanced_agent import EnhancedLegalAgent
from comp2.src.retrieval.chroma_store import ChromaStore
from comp2.api.config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL_NAME,
    FINE_TUNED_MODEL_PATH,
)

logger = logging.getLogger(__name__)


def _build_case_info_from_chroma(
    chroma_id: str,
    meta: Dict,
    document: str,
) -> Dict[str, Any]:
    """Build case_info dict from ChromaDB search result (metadata + document)."""
    case_id = meta.get("case_id", chroma_id) if meta else chroma_id
    # Extract case_id from chroma_id if format is "case_id_index"
    if "_" in str(case_id) and meta and "case_id" in meta:
        case_id = meta["case_id"]
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


class AnalysisService:
    """Service for processing legal case analysis - ChromaDB-only"""

    def __init__(self):
        """Initialize all ML components"""
        logger.info("Initializing Analysis Service (ChromaDB-only)...")

        try:
            self.processor = MultiFormatProcessor()
            logger.info("[OK] Document processor initialized")

            self.cleaner = TextCleaner()
            logger.info("[OK] Text cleaner initialized")

            if FINE_TUNED_MODEL_PATH:
                logger.info(f"Using fine-tuned Legal-BERT from: {FINE_TUNED_MODEL_PATH}")
                self.feature_extractor = FeatureExtractor(fine_tuned_model_path=FINE_TUNED_MODEL_PATH)
            else:
                logger.info(f"Using Legal-BERT (pre-trained): {EMBEDDING_MODEL_NAME}")
                self.feature_extractor = FeatureExtractor(model_name=EMBEDDING_MODEL_NAME)
            logger.info("[OK] Feature extractor initialized with Legal-BERT")

            # ChromaDB and ClusterPredictor: lazy init (only needed for arguments/process, not for case analysis)
            self._chroma_store = None
            self._cluster_predictor = None

            # Initialize LLM client and enhanced agent
            try:
                self.llm_client = LLMClient(provider="groq")
                self.enhanced_agent = EnhancedLegalAgent(
                    self.llm_client,
                    use_model_arguments=True,
                    model_only_mode=False,  # Use LLM for rich arguments + adversarial simulation
                )
                logger.info(f"[OK] LLM client initialized: {self.llm_client.provider}")
                logger.info("[OK] Model-only argument generation enabled")
            except Exception as e:
                logger.warning(f"[WARN] LLM client initialization failed: {e}")
                self.llm_client = None
                self.enhanced_agent = None

            logger.info("[OK] Analysis Service initialized successfully")

        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize Analysis Service: {e}")
            raise

    def _get_chroma_store(self):
        """Lazy init ChromaDB (required for arguments/process, not for case analysis)."""
        if self._chroma_store is None:
            if not CHROMA_PERSIST_DIR.exists():
                raise FileNotFoundError(
                    f"ChromaDB directory not found at {CHROMA_PERSIST_DIR}. "
                    "Run backend2 Notebook 03 to populate ChromaDB, then copy chroma_db to backend/data/chroma_db_comp2/"
                )
            self._chroma_store = ChromaStore(
                persist_directory=str(CHROMA_PERSIST_DIR),
                collection_name=CHROMA_COLLECTION_NAME,
            )
            count = self._chroma_store.count()
            if count == 0:
                raise FileNotFoundError(
                    f"ChromaDB collection '{CHROMA_COLLECTION_NAME}' is empty. "
                    "Run backend2 Notebook 03 to populate ChromaDB, then copy chroma_db to backend/data/chroma_db_comp2/"
                )
            logger.info(f"[OK] ChromaDB loaded ({count} vectors)")
        return self._chroma_store

    def _get_cluster_predictor(self):
        """Lazy init K-Means cluster predictor (required for arguments/process)."""
        if self._cluster_predictor is None:
            self._cluster_predictor = ClusterPredictor()
        return self._cluster_predictor

    def _find_similar_cases(
        self,
        embedding: np.ndarray,
        top_k: int,
    ) -> Tuple[List[Dict], List[str], List[float]]:
        """Find similar cases using ChromaDB. Returns (similar_cases, case_ids, distances)."""
        chroma_store = self._get_chroma_store()
        ids, distances, metadatas, documents = chroma_store.search(
            embedding, n_results=top_k
        )
        similar_cases = []
        similar_case_ids = []
        distances_list = []

        for i, (cid, dist) in enumerate(zip(ids, distances)):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc = documents[i] if documents and i < len(documents) else ""
            case_info = _build_case_info_from_chroma(cid, meta, doc)
            case_id = case_info["case_id"]
            similar_case_ids.append(case_id)
            distances_list.append(float(dist))
            similar_cases.append(case_info)

        return similar_cases, similar_case_ids, distances_list

    def _build_case_dict(self, similar_cases: List[Dict], similar_case_ids: List[str]) -> Dict:
        """Build case_dict for argument report from similar_cases."""
        return {cid: case for cid, case in zip(similar_case_ids, similar_cases)}

    async def process_case(
        self,
        job_id: str = None,
        file_path: str = None,
        top_k: int = 10,
    ):
        """Process a case file through the complete pipeline."""
        try:
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text(file_path)
            case_text = doc_data.get("full_text", "")

            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")

            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)

            logger.info("Generating text embeddings using Legal-BERT...")
            embedding = self.feature_extractor.extract_embeddings(
                [cleaned_text], show_progress=False
            )

            logger.info(f"Finding similar cases (top_k={top_k})...")
            similar_cases, similar_case_ids, distances_list = self._find_similar_cases(
                embedding, top_k
            )
            logger.info(f"Found {len(similar_cases)} similar cases")

            cluster_id = self._get_cluster_predictor().predict_cluster(embedding)

            input_metadata = None
            full_json_data = None
            if isinstance(doc_data, dict) and "json_data" in doc_data:
                json_data = doc_data.get("json_data", {})
                if isinstance(json_data, dict):
                    input_metadata = json_data.get("input_metadata")
                    full_json_data = json_data

            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate analysis.")

            logger.info("Generating comprehensive case analysis...")
            analyzed_case_file = self.enhanced_agent.generate_analyzed_case_file(
                cleaned_text,
                input_metadata=input_metadata,
                full_json_data=full_json_data,
            )

            logger.info("Generating strategic arguments report...")
            case_dict = self._build_case_dict(similar_cases, similar_case_ids)
            arguments_report = self.enhanced_agent.generate_arguments_report(
                cleaned_text,
                similar_cases,
                similar_case_ids,
                distances=distances_list,
                case_dict=case_dict,
                cluster_id=cluster_id,
            )

            logger.info("Analysis completed successfully")
            return analyzed_case_file, arguments_report

        except Exception as e:
            logger.error(f"Error during processing - {str(e)}")
            raise

    async def analyze_case(self, file_path: str):
        """
        Analyze a case file and generate comprehensive case analysis (Output File 1).
        Uses LLM only - no ChromaDB or similar cases needed.
        Returns analyzed_case, document_text, source_spans for document viewer.
        """
        from comp2.src.document_processing.source_mapper import SourceMapper

        try:
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text_with_positions(file_path)
            case_text = doc_data.get("full_text", "")
            pages = doc_data.get("pages", [])

            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")

            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)

            input_metadata = None
            full_json_data = None
            if isinstance(doc_data, dict) and "json_data" in doc_data:
                json_data = doc_data.get("json_data", {})
                if isinstance(json_data, dict):
                    input_metadata = json_data.get("input_metadata")
                    full_json_data = json_data

            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate analysis.")

            logger.info("Generating comprehensive case analysis...")
            analyzed_case_file = self.enhanced_agent.generate_analyzed_case_file(
                cleaned_text,
                input_metadata=input_metadata,
                full_json_data=full_json_data,
            )

            logger.info("Mapping extracted fields to source text positions...")
            source_spans = []
            try:
                mapper = SourceMapper(case_text, pages)
                source_spans = mapper.map_fields(analyzed_case_file)
            except Exception as e:
                logger.warning(f"Source mapping failed (non-fatal): {e}")

            document_text = [{"page_num": p["page_num"], "text": p["text"]} for p in pages]

            logger.info("Case analysis completed successfully")
            return {
                **analyzed_case_file,
                "document_text": document_text,
                "source_spans": source_spans,
            }

        except Exception as e:
            logger.error(f"Error during case analysis - {str(e)}")
            raise

    async def generate_arguments(self, file_path: str):
        """Generate argument points and strategic arguments report (Output File 2)."""
        DEFAULT_SIMILAR_CASES = 10

        try:
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text(file_path)
            case_text = doc_data.get("full_text", "")

            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")

            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)

            logger.info("Generating text embeddings using Legal-BERT...")
            embedding = self.feature_extractor.extract_embeddings(
                [cleaned_text], show_progress=False
            )

            logger.info("Finding similar cases...")
            similar_cases, similar_case_ids, distances_list = self._find_similar_cases(
                embedding, DEFAULT_SIMILAR_CASES
            )
            logger.info(f"Found {len(similar_cases)} similar cases")

            cluster_id = self._get_cluster_predictor().predict_cluster(embedding)

            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate arguments.")

            logger.info("Generating strategic arguments report...")
            case_dict = self._build_case_dict(similar_cases, similar_case_ids)
            arguments_report = self.enhanced_agent.generate_arguments_report(
                cleaned_text,
                similar_cases,
                similar_case_ids,
                distances=distances_list,
                case_dict=case_dict,
                cluster_id=cluster_id,
            )

            logger.info("Arguments generation completed successfully")
            return arguments_report

        except Exception as e:
            logger.error(f"Error during arguments generation - {str(e)}")
            raise


_analysis_service = None


def get_analysis_service() -> AnalysisService:
    """Get or create the analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
