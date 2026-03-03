"""
Main prediction model for Appeal Outcome Decision Support
"""
import pickle
import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging

from .bert_processor import BERTProcessor
from .feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)

class AppealPredictor:
    """Main prediction model for appeal outcomes"""
    
    def __init__(self, 
                 model_path: str,
                 selector_path: str,
                 label_encoder_path: str,
                 x_train_path: str,
                 bert_embeddings_path: str,
                 dataset_path: str,
                 y_train_path: str,
                 bert_model_name: str = "nlpaueb/legal-bert-base-uncased"):
        """
        Initialize the appeal predictor with all required models and data
        
        Args:
            model_path: Path to the trained prediction model
            selector_path: Path to feature selector
            label_encoder_path: Path to label encoder
            x_train_path: Path to training features
            bert_embeddings_path: Path to BERT embeddings
            dataset_path: Path to case dataset
            y_train_path: Path to training labels
            bert_model_name: Name of BERT model to use
        """
        self.model_path = model_path
        self.selector_path = selector_path
        self.label_encoder_path = label_encoder_path
        self.x_train_path = x_train_path
        self.bert_embeddings_path = bert_embeddings_path
        self.dataset_path = dataset_path
        self.y_train_path = y_train_path
        
        # Initialize components
        self.bert_processor = None
        self.feature_extractor = FeatureExtractor()
        
        # Load models and data
        self._load_models()
        self._load_data()
        
        # Initialize BERT processor
        self.bert_processor = BERTProcessor(bert_model_name)
        
        logger.info("AppealPredictor initialized successfully")
    
    def _load_models(self):
        """Load ML models and encoders"""
        try:
            # Load main model
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            if isinstance(model_data, dict):
                self.model = model_data['model']
                self.scaler = model_data.get('scaler')
            else:
                self.model = model_data
                self.scaler = None
            
            # Load feature selector
            with open(self.selector_path, 'rb') as f:
                self.selector = pickle.load(f)
            
            # Load label encoder
            with open(self.label_encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def _load_data(self):
        """Load training data and embeddings"""
        try:
            # Load training features
            self.X_train_full = pd.read_csv(self.x_train_path)
            
            # Load BERT embeddings
            self.train_embeddings = np.load(self.bert_embeddings_path)
            
            # Load case dataset
            self.df_cases = pd.read_csv(self.dataset_path)
            
            # Load training labels
            self.y_train = np.load(self.y_train_path)
            
            logger.info("Data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def predict_appeal(self, case_description: str) -> Dict[str, Any]:
        """
        Predict appeal outcome for a given case description
        
        Args:
            case_description: Detailed case description
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Extract traditional features
            traditional_features = self.feature_extractor.extract_features_from_text(
                case_description, self.X_train_full.columns
            )
            
            # Generate BERT embedding
            bert_features = self.bert_processor.get_embedding(case_description)
            
            # Combine features
            all_features = np.concatenate([traditional_features, bert_features])
            
            # Create DataFrame with proper column names
            df_features = pd.DataFrame(
                all_features.reshape(1, -1),
                columns=self.X_train_full.columns
            )
            
            # Apply feature selection
            selected_features = self.selector.transform(df_features)
            
            # Scale if scaler exists
            if self.scaler is not None:
                selected_features = self.scaler.transform(selected_features)
            
            # Make prediction
            probabilities = self.model.predict_proba(selected_features)[0]
            prediction = self.model.predict(selected_features)[0]
            predicted_class = self.label_encoder.inverse_transform([prediction])[0]
            
            # Detect features for display
            detected_features = self.feature_extractor.detect_active_features(
                case_description, self.X_train_full.columns
            )
            
            # Create result dictionary
            result = {
                'probabilities': {
                    'Appeal_Allowed': float(probabilities[0] * 100),
                    'Appeal_Dismissed': float(probabilities[1] * 100),
                    'Partly_Allowed': float(probabilities[2] * 100)
                },
                'prediction': predicted_class,
                'confidence': float(max(probabilities) * 100),
                'bert_embedding': bert_features,
                'detected_features': detected_features
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            raise
    
    def find_similar_cases(self, bert_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar historical cases based on BERT embedding similarity
        
        Args:
            bert_embedding: BERT embedding of the current case
            top_k: Number of similar cases to return
            
        Returns:
            List of similar cases with details
        """
        try:
            # Calculate similarities
            similarities = cosine_similarity(
                bert_embedding.reshape(1, -1),
                self.train_embeddings
            )[0]
            
            # Get top k most similar cases
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            similar_cases = []
            for idx in top_indices:
                case = self.df_cases.iloc[idx]
                outcome = self.label_encoder.inverse_transform([self.y_train[idx]])[0]
                
                # Extract case details with proper handling of missing values
                case_facts = str(case.get('brief_facts_summary', 'Details not available'))
                conviction_status = str(case.get('coa_conviction_status', 'Not specified'))
                case_number = str(case.get('ca_number', f"Case_{idx}"))
                offence = str(case.get('offence_category', 'Not specified'))
                high_court = str(case.get('high_court_location', 'Not specified'))
                grounds = str(case.get('grounds_of_appeal_summary', 'Not specified'))
                
                # Clean up 'nan' values
                for field_name, field_value in [
                    ('conviction_status', conviction_status),
                    ('case_number', case_number),
                    ('offence', offence),
                    ('high_court', high_court),
                    ('grounds', grounds)
                ]:
                    if field_value in ['nan', 'None', '']:
                        if field_name == 'case_number':
                            field_value = f"Case_{idx}"
                        else:
                            field_value = 'Not specified'
                
                # Truncate grounds if too long
                if grounds != 'Not specified' and len(grounds) > 300:
                    grounds = grounds[:300] + "..."
                
                similar_cases.append({
                    'case_id': case_number,
                    'similarity': float(similarities[idx] * 100),
                    'outcome': outcome,
                    'conviction_status': conviction_status,
                    'facts': case_facts,
                    'offence': offence,
                    'high_court': high_court,
                    'grounds': grounds
                })
            
            return similar_cases
            
        except Exception as e:
            logger.error(f"Error finding similar cases: {e}")
            raise
    
    def get_model_metadata(self) -> Dict[str, Any]:
        """
        Get model metadata information
        
        Returns:
            Dictionary with model metadata
        """
        try:
            # Try to load metadata from JSON file in comp3 directory
            metadata_path = self.model_path.parent / 'model_metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default metadata
                return {
                    'accuracy': 0.6255,
                    'model_name': 'XGBoost Custom Weights',
                    'training_date': '2026-01-06',
                    'training_samples': 1000,
                    'num_features': 150
                }
        except:
            return {
                'accuracy': 0.6255,
                'model_name': 'XGBoost Custom Weights',
                'training_date': '2026-01-06',
                'training_samples': 1000,
                'num_features': 150
            }
