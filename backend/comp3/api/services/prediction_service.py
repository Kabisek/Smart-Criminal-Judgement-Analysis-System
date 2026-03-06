"""
Prediction service for Appeal Outcome Decision Support
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from comp3.src.core.models import AppealPredictor
from comp3.api.config import (
    MODEL_PATH,
    SELECTOR_PATH,
    LABEL_ENCODER_PATH,
    X_TRAIN_PATH,
    BERT_EMBEDDINGS_PATH,
    DATASET_PATH,
    Y_TRAIN_PATH,
    TFIDF_VECTORIZER_PATH,
    SCALER_PATH,
    SIMILAR_CASES_TOP_K,
    DEFAULT_METADATA
)

logger = logging.getLogger(__name__)

class PredictionService:
    """Service for handling appeal outcome predictions"""
    
    def __init__(self):
        """Initialize the prediction service"""
        self.predictor = None
        self._initialize_predictor()
    
    def _initialize_predictor(self):
        """Initialize the appeal predictor"""
        try:
            logger.info("Initializing AppealPredictor...")
            
            # Check if all required files exist
            required_files = [
                MODEL_PATH,
                SELECTOR_PATH,
                LABEL_ENCODER_PATH,
                X_TRAIN_PATH,
                BERT_EMBEDDINGS_PATH,
                DATASET_PATH,
                Y_TRAIN_PATH,
                TFIDF_VECTORIZER_PATH,
                SCALER_PATH
            ]
            
            missing_files = []
            for file_path in required_files:
                if not file_path.exists():
                    missing_files.append(str(file_path))
            
            if missing_files:
                raise FileNotFoundError(f"Missing required model files: {missing_files}")
            
            # Initialize predictor
            self.predictor = AppealPredictor(
                model_path=MODEL_PATH,
                selector_path=SELECTOR_PATH,
                label_encoder_path=LABEL_ENCODER_PATH,
                x_train_path=X_TRAIN_PATH,
                bert_embeddings_path=BERT_EMBEDDINGS_PATH,
                dataset_path=DATASET_PATH,
                y_train_path=Y_TRAIN_PATH
            )
            
            logger.info("AppealPredictor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AppealPredictor: {e}")
            raise
    
    async def predict_appeal_outcome(self, case_description: str) -> Dict[str, Any]:
        """
        Predict appeal outcome for a given case description
        
        Args:
            case_description: Detailed case description
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.predictor:
                raise RuntimeError("Predictor not initialized")
            
            logger.info(f"Starting prediction for case description length: {len(case_description)}")
            
            # Get prediction
            prediction_result = self.predictor.predict_appeal(case_description)
            
            # Find similar cases
            similar_cases = self.predictor.find_similar_cases(
                prediction_result['bert_embedding'],
                top_k=SIMILAR_CASES_TOP_K
            )
            
            # Get model metadata
            metadata = self.predictor.get_model_metadata()
            
            # Create final response
            response = {
                'status': 'success',
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'probabilities': prediction_result['probabilities'],
                'detected_features': prediction_result['detected_features'],
                'similar_cases': similar_cases,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Prediction completed: {prediction_result['prediction']} with {prediction_result['confidence']:.1f}% confidence")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in predict_appeal_outcome: {e}")
            raise
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and status
        
        Returns:
            Dictionary with model information
        """
        try:
            if not self.predictor:
                return {
                    'status': 'not_initialized',
                    'message': 'Model not loaded',
                    'timestamp': datetime.now().isoformat()
                }
            
            metadata = self.predictor.get_model_metadata()
            
            return {
                'status': 'ready',
                'metadata': metadata,
                'model_files': {
                    'model': str(MODEL_PATH),
                    'selector': str(SELECTOR_PATH),
                    'label_encoder': str(LABEL_ENCODER_PATH),
                    'training_data': str(DATASET_PATH)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Singleton instance
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """Get or create the prediction service singleton"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
