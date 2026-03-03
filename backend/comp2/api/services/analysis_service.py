"""
Analysis Service
Orchestrates the complete ML pipeline for case analysis
"""
import sys
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
import logging

# Add backend root to path (comp2/api/services → backend/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from comp2.src.document_processing.processor import MultiFormatProcessor
from comp2.src.ml_utils.feature_extractor import FeatureExtractor
from comp2.src.ml_utils.text_cleaner import TextCleaner
from comp2.src.llm.client import LLMClient
from comp2.src.reasoning.enhanced_agent import EnhancedLegalAgent
from comp2.api.config import (
    FEATURE_VECTORS_PATH,
    NEAREST_NEIGHBORS_MODEL_PATH,
    CLEANED_CASES_CSV_PATH,
    EMBEDDING_MODEL_NAME,
    FINE_TUNED_MODEL_PATH
)

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for processing legal case analysis"""
    
    def __init__(self):
        """Initialize all ML components"""
        logger.info("Initializing Analysis Service...")
        
        try:
            # Initialize document processor
            self.processor = MultiFormatProcessor()
            logger.info("✅ Document processor initialized")
            
            # Initialize text cleaner
            self.cleaner = TextCleaner()
            logger.info("✅ Text cleaner initialized")
            
            # Initialize feature extractor with Legal-BERT (from config)
            # Use fine-tuned model if available, otherwise use pre-trained Legal-BERT
            if FINE_TUNED_MODEL_PATH:
                logger.info(f"Using fine-tuned Legal-BERT from: {FINE_TUNED_MODEL_PATH}")
                self.feature_extractor = FeatureExtractor(fine_tuned_model_path=FINE_TUNED_MODEL_PATH)
            else:
                logger.info(f"Using Legal-BERT (pre-trained): {EMBEDDING_MODEL_NAME}")
                self.feature_extractor = FeatureExtractor(model_name=EMBEDDING_MODEL_NAME)
            logger.info("✅ Feature extractor initialized with Legal-BERT")
            
            # Load feature vectors
            if not FEATURE_VECTORS_PATH.exists():
                raise FileNotFoundError(f"Feature vectors not found at {FEATURE_VECTORS_PATH}")
            
            self.embeddings, self.case_ids = self.feature_extractor.load_features(
                str(FEATURE_VECTORS_PATH)
            )
            logger.info(f"✅ Loaded {len(self.case_ids)} case embeddings")
            
            # Load Nearest Neighbors model
            if not NEAREST_NEIGHBORS_MODEL_PATH.exists():
                raise FileNotFoundError(f"NN model not found at {NEAREST_NEIGHBORS_MODEL_PATH}")
            
            with open(NEAREST_NEIGHBORS_MODEL_PATH, 'rb') as f:
                self.nn_model = pickle.load(f)
            logger.info("✅ Nearest Neighbors model loaded")
            
            # Load processed cases data
            if not CLEANED_CASES_CSV_PATH.exists():
                raise FileNotFoundError(f"Cleaned cases CSV not found at {CLEANED_CASES_CSV_PATH}")
            
            self.df_cases = pd.read_csv(CLEANED_CASES_CSV_PATH)
            self.case_dict = {
                row['case_id']: row.to_dict() 
                for _, row in self.df_cases.iterrows()
            }
            logger.info(f"✅ Loaded {len(self.case_dict)} case records")
            
            # Initialize LLM client and enhanced agent
            try:
                self.llm_client = LLMClient(provider="groq")
                # Use LLM for argument generation (model_only_mode=False enables LLM-based arguments)
                self.enhanced_agent = EnhancedLegalAgent(
                    self.llm_client, 
                    use_model_arguments=True,
                    model_only_mode=False  # Use LLM for argument generation
                )
                logger.info(f"✅ LLM client initialized: {self.llm_client.provider}")
                logger.info("✅ LLM-based argument generation enabled (Groq + model patterns)")
            except Exception as e:
                logger.warning(f"⚠️ LLM client initialization failed: {e}")
                self.llm_client = None
                self.enhanced_agent = None
            
            logger.info("✅ Analysis Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Analysis Service: {e}")
            raise
    
    async def process_case(self, job_id: str = None, file_path: str = None, top_k: int = 10):
        """
        Process a case file through the complete pipeline (synchronous processing)
        
        Args:
            job_id: Optional job ID for tracking (not required for sync processing)
            file_path: Path to the case file
            top_k: Number of similar cases to retrieve
            
        Returns:
            tuple: (analyzed_case_file, arguments_report)
        """
        try:
            # Stage 1: Extract text
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text(file_path)
            case_text = doc_data.get('full_text', '')
            
            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")
            
            # Stage 2: Clean text
            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)
            
            # Stage 3: Generate embedding
            logger.info("Generating text embeddings using Legal-BERT...")
            embedding = self.feature_extractor.extract_embeddings(
                [cleaned_text], 
                show_progress=False
            )
            
            # Stage 4: Find similar cases
            logger.info(f"Finding similar cases (top_k={top_k})...")
            n_neighbors = min(top_k, len(self.case_ids))
            distances, indices = self.nn_model.kneighbors(
                embedding, 
                n_neighbors=n_neighbors
            )
            
            similar_cases = []
            similar_case_ids = []
            for idx, distance in zip(indices[0], distances[0]):
                case_id = self.case_ids[idx]
                similar_case_ids.append(case_id)
                case_info = self.case_dict.get(case_id, {})
                similar_cases.append(case_info)
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            # Stage 5: Generate Output File 1 (Analyzed Case File)
            logger.info("Generating comprehensive case analysis...")
            
            # Extract input metadata if available (for JSON inputs)
            input_metadata = None
            full_json_data = None
            if isinstance(doc_data, dict) and 'json_data' in doc_data:
                json_data = doc_data.get('json_data', {})
                if isinstance(json_data, dict):
                    input_metadata = json_data.get('input_metadata')
                    full_json_data = json_data
            
            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate analysis.")
            
            analyzed_case_file = self.enhanced_agent.generate_analyzed_case_file(
                cleaned_text,
                input_metadata=input_metadata,
                full_json_data=full_json_data
            )
            
            # Stage 6: Generate Output File 2 (Arguments Report)
            logger.info("Generating strategic arguments report...")
            
            similar_distances = distances[0].tolist()[:len(similar_case_ids)]
            arguments_report = self.enhanced_agent.generate_arguments_report(
                cleaned_text,
                similar_cases,
                similar_case_ids,
                distances=similar_distances,
                case_dict=self.case_dict
            )
            
            logger.info("Analysis completed successfully")
            return analyzed_case_file, arguments_report
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during processing - {error_msg}")
            raise
    
    async def analyze_case(self, file_path: str):
        """
        Analyze a case file and generate comprehensive case analysis (Output File 1).

        Returns a dict with keys:
            analyzed_case  – the LLM-generated case structure
            document_text  – list of page texts (for the document viewer)
            source_spans   – list of {field_id, page, start_char, end_char, matched_text}
        """
        from comp2.src.document_processing.source_mapper import SourceMapper

        DEFAULT_SIMILAR_CASES = 10
        
        try:
            # Stage 1: Extract text WITH position data
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text_with_positions(file_path)
            case_text = doc_data.get('full_text', '')
            pages = doc_data.get('pages', [])
            
            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")
            
            # Stage 2: Clean text
            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)
            
            # Stage 3: Generate embedding
            logger.info("Generating text embeddings using Legal-BERT...")
            embedding = self.feature_extractor.extract_embeddings(
                [cleaned_text], 
                show_progress=False
            )
            
            # Stage 4: Find similar cases
            logger.info(f"Finding similar cases...")
            n_neighbors = min(DEFAULT_SIMILAR_CASES, len(self.case_ids))
            distances, indices = self.nn_model.kneighbors(
                embedding, 
                n_neighbors=n_neighbors
            )
            
            similar_cases = []
            similar_case_ids = []
            for idx, distance in zip(indices[0], distances[0]):
                case_id = self.case_ids[idx]
                similar_case_ids.append(case_id)
                case_info = self.case_dict.get(case_id, {})
                similar_cases.append(case_info)
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            # Stage 5: Generate Output File 1 (Analyzed Case File)
            logger.info("Generating comprehensive case analysis...")
            
            input_metadata = None
            full_json_data = None
            if isinstance(doc_data, dict) and 'json_data' in doc_data:
                json_data = doc_data.get('json_data', {})
                if isinstance(json_data, dict):
                    input_metadata = json_data.get('input_metadata')
                    full_json_data = json_data
            
            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate analysis.")
            
            analyzed_case_file = self.enhanced_agent.generate_analyzed_case_file(
                cleaned_text,
                input_metadata=input_metadata,
                full_json_data=full_json_data
            )

            # Stage 6: Map extracted fields back to source text positions
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
            error_msg = str(e)
            logger.error(f"Error during case analysis - {error_msg}")
            raise
    
    async def generate_arguments(self, file_path: str):
        """
        Generate argument points and strategic arguments report (Output File 2)
        
        Args:
            file_path: Path to the case file
            
        Returns:
            Dict: Arguments report data
        """
        # Default number of similar cases to find (removed top_k parameter)
        DEFAULT_SIMILAR_CASES = 10
        
        try:
            # Stage 1: Extract text
            logger.info(f"Extracting text from {file_path}")
            doc_data = self.processor.extract_text(file_path)
            case_text = doc_data.get('full_text', '')
            
            if not case_text or len(case_text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")
            
            # Stage 2: Clean text
            logger.info("Cleaning and preprocessing text...")
            cleaned_text = self.cleaner.clean_text(case_text)
            
            # Stage 3: Generate embedding
            logger.info("Generating text embeddings using Legal-BERT...")
            embedding = self.feature_extractor.extract_embeddings(
                [cleaned_text], 
                show_progress=False
            )
            
            # Stage 4: Find similar cases
            logger.info(f"Finding similar cases...")
            n_neighbors = min(DEFAULT_SIMILAR_CASES, len(self.case_ids))
            distances, indices = self.nn_model.kneighbors(
                embedding, 
                n_neighbors=n_neighbors
            )
            
            similar_cases = []
            similar_case_ids = []
            for idx, distance in zip(indices[0], distances[0]):
                case_id = self.case_ids[idx]
                similar_case_ids.append(case_id)
                case_info = self.case_dict.get(case_id, {})
                similar_cases.append(case_info)
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            # Stage 5: Generate Output File 2 (Arguments Report)
            logger.info("Generating strategic arguments report...")
            
            if not self.enhanced_agent:
                raise RuntimeError("LLM client not initialized. Cannot generate arguments.")
            
            similar_distances = distances[0].tolist()[:len(similar_case_ids)]
            arguments_report = self.enhanced_agent.generate_arguments_report(
                cleaned_text,
                similar_cases,
                similar_case_ids,
                distances=similar_distances,
                case_dict=self.case_dict
            )
            
            logger.info("Arguments generation completed successfully")
            return arguments_report
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during arguments generation - {error_msg}")
            raise

# Global analysis service instance (lazy initialization)
_analysis_service = None

def get_analysis_service() -> AnalysisService:
    """Get or create the analysis service instance"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service
