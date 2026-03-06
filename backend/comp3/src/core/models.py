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
            # Load main model (improved ensemble)
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load scaler separately for improved model
            try:
                scaler_path = self.model_path.parent / 'improved_scaler.pkl'
                if scaler_path.exists():
                    with open(scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                else:
                    self.scaler = None
            except:
                self.scaler = None
            
            # Load feature selector
            with open(self.selector_path, 'rb') as f:
                self.selector = pickle.load(f)
            
            # Load label encoder
            with open(self.label_encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            # Load TF-IDF vectorizer if available
            try:
                tfidf_path = self.model_path.parent / 'improved_tfidf_vectorizer.pkl'
                if tfidf_path.exists():
                    with open(tfidf_path, 'rb') as f:
                        self.tfidf_vectorizer = pickle.load(f)
                else:
                    self.tfidf_vectorizer = None
            except:
                self.tfidf_vectorizer = None
            
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
            # Step 1: Generate TF-IDF features
            tfidf_dict = {}
            if self.tfidf_vectorizer is not None:
                tfidf_matrix = self.tfidf_vectorizer.transform([case_description])
                tfidf_array = tfidf_matrix.toarray()[0]
                tfidf_feature_names = [f'tfidf_{feature}' for feature in self.tfidf_vectorizer.get_feature_names_out()]
                tfidf_dict = dict(zip(tfidf_feature_names, tfidf_array))
                logger.info(f"TF-IDF dictionary created with {len(tfidf_dict)} features")
            
            # Step 2: Generate BERT embedding
            bert_features = self.bert_processor.get_embedding(case_description)
            bert_dict = {f'bert_{i}': val for i, val in enumerate(bert_features)}
            logger.info(f"BERT dictionary created with {len(bert_dict)} features")
            
            # Step 3: Extract traditional features
            traditional_dict = {}
            traditional_cols = [col for col in self.X_train_full.columns 
                             if not col.startswith('bert_') and not col.startswith('tfidf_')]
            
            text = case_description.lower()
            
            # Extract traditional features using the same logic as demo
            for col in traditional_cols:
                if col == 'brief_facts_summary_length':
                    traditional_dict[col] = len(text)
                elif col == 'brief_facts_summary_word_count':
                    traditional_dict[col] = len(text.split())
                elif col == 'grounds_of_appeal_raw_text_summary_length':
                    traditional_dict[col] = len(text) * 0.4
                elif col == 'grounds_of_appeal_raw_text_summary_word_count':
                    traditional_dict[col] = len(text.split()) * 0.4
                elif col == 'court_of_appeal_analysis_summary_length':
                    traditional_dict[col] = len(text) * 0.3
                elif col == 'court_of_appeal_analysis_summary_word_count':
                    traditional_dict[col] = len(text.split()) * 0.3
                elif col.startswith('gnd_'):
                    # Handle grounds features
                    if 'contradictions' in col and any(kw in text for kw in ['contradiction', 'inconsistent', 'conflicting']):
                        traditional_dict[col] = 1.0
                    elif 'chain_of_custody' in col and any(kw in text for kw in ['chain of custody', 'custody', 'preservation']):
                        traditional_dict[col] = 1.0
                    elif 'illegal_search' in col and any(kw in text for kw in ['illegal search', 'unlawful search', 'search raid']):
                        traditional_dict[col] = 1.0
                    elif 'wrong_identification' in col and any(kw in text for kw in ['identification', 'identify', 'mistaken identity']):
                        traditional_dict[col] = 1.0
                    elif 'dying_declaration' in col and any(kw in text for kw in ['dying declaration', 'deathbed statement']):
                        traditional_dict[col] = 1.0
                    elif 'circumstantial' in col and any(kw in text for kw in ['circumstantial', 'indirect evidence']):
                        traditional_dict[col] = 1.0
                    elif 'medical_inconsistency' in col and any(kw in text for kw in ['medical', 'jmo', 'post-mortem']):
                        traditional_dict[col] = 1.0
                    elif 'misdirection' in col and any(kw in text for kw in ['misdirection', 'wrong direction', 'legal error']):
                        traditional_dict[col] = 1.0
                    elif 'procedural_error' in col and any(kw in text for kw in ['procedural', 'procedure', 'process error']):
                        traditional_dict[col] = 1.0
                    elif 'new_evidence' in col and any(kw in text for kw in ['new evidence', 'fresh evidence']):
                        traditional_dict[col] = 1.0
                    elif 'excessive_sentence' in col and any(kw in text for kw in ['excessive', 'harsh', 'inadequate sentence']):
                        traditional_dict[col] = 1.0
                    elif 'delay_prejudice' in col and any(kw in text for kw in ['delay', 'prejudice', 'lapse of time']):
                        traditional_dict[col] = 1.0
                    elif 'judicial_bias' in col and any(kw in text for kw in ['bias', 'unfair', 'prejudiced judge']):
                        traditional_dict[col] = 1.0
                    else:
                        traditional_dict[col] = 0.0
                elif col.startswith('eyewitness_') or 'eyewitness_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['eyewitness', 'witness', 'testimony']))
                elif col.startswith('child_witness_') or 'child_witness_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['child witness', 'minor witness']))
                elif col.startswith('expert_evidence_') or 'expert_evidence_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['expert', 'jmo', 'analyst', 'specialist']))
                elif col.startswith('forensic_evidence_') or 'forensic_evidence_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['forensic', 'dna', 'fingerprint', 'ballistic']))
                elif col.startswith('dying_declaration_present'):
                    traditional_dict[col] = float(any(kw in text for kw in ['dying declaration']))
                elif col.startswith('confession_') or 'confession_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['confession', 'admitted', 'dock statement']))
                elif col.startswith('procedural_defects_') or 'procedural_defects_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['procedural defect', 'process error', 'procedural']))
                elif col.startswith('digital_evidence_') or 'digital_evidence_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['cctv', 'phone', 'digital', 'video', 'recording']))
                elif col.startswith('hospital_treatment_') or 'hospital_treatment_details_present' in col:
                    traditional_dict[col] = float(any(kw in text for kw in ['hospital', 'medical treatment', 'admitted to hospital']))
                elif col == 'medical_evidence_score':
                    medical_terms = ['medical', 'jmo', 'post-mortem', 'autopsy', 'pathologist', 'medical evidence']
                    traditional_dict[col] = float(sum(1 for term in medical_terms if term in text))
                elif col.startswith('offence_category_'):
                    # Handle offence categories
                    if 'Murder_Related' in col and any(kw in text for kw in ['murder', '296', 'homicide', 'culpable homicide']):
                        traditional_dict[col] = 1.0
                    elif 'Sexual_Offenses' in col and any(kw in text for kw in ['rape', 'sexual', '363', '365', 'abuse']):
                        traditional_dict[col] = 1.0
                    elif 'Drug_Related' in col and any(kw in text for kw in ['drug', 'narcotic', 'poisons', 'opium act', 'heroin']):
                        traditional_dict[col] = 1.0
                    elif 'Robbery_Theft' in col and any(kw in text for kw in ['robbery', 'theft', 'burglary', '380', '394']):
                        traditional_dict[col] = 1.0
                    elif 'Fraud_Corruption' in col and any(kw in text for kw in ['fraud', 'corruption', 'bribery', 'cheating']):
                        traditional_dict[col] = 1.0
                    elif 'Firearms_Weapons' in col and any(kw in text for kw in ['firearm', 'weapon', 'explosives']):
                        traditional_dict[col] = 1.0
                    elif 'Traffic_Vehicle' in col and any(kw in text for kw in ['traffic', 'vehicle', 'rash driving']):
                        traditional_dict[col] = 1.0
                    elif 'Environmental' in col and any(kw in text for kw in ['environment', 'wildlife', 'forest']):
                        traditional_dict[col] = 1.0
                    elif 'Customs' in col and any(kw in text for kw in ['customs', 'import', 'export']):
                        traditional_dict[col] = 1.0
                    else:
                        traditional_dict[col] = 0.0
                elif col.startswith('appeal_type_'):
                    # Handle appeal types
                    if 'Conviction_Only' in col and any(kw in text for kw in ['conviction', 'acquittal']):
                        traditional_dict[col] = 1.0
                    elif 'Sentence_Only' in col and any(kw in text for kw in ['sentence', 'penalty', 'punishment']):
                        traditional_dict[col] = 1.0
                    elif 'Revision' in col and any(kw in text for kw in ['revision', 'review']):
                        traditional_dict[col] = 1.0
                    elif 'Writ' in col and any(kw in text for kw in ['writ', 'certiorari', 'mandamus']):
                        traditional_dict[col] = 1.0
                    else:
                        traditional_dict[col] = 0.0
                elif col == 'coa_year':
                    traditional_dict[col] = 2024.0
                elif col == 'appeal_duration_days':
                    traditional_dict[col] = 730.0
                elif col == 'evidence_count':
                    evidence_cols = [c for c in traditional_cols if 'present' in c]
                    traditional_dict[col] = sum(traditional_dict.get(c, 0) for c in evidence_cols)
                else:
                    traditional_dict[col] = 0.0
            
            logger.info(f"Traditional dictionary created with {len(traditional_dict)} features")
            
            # Step 4: Combine all features
            all_features = {**traditional_dict, **tfidf_dict, **bert_dict}
            logger.info(f"Combined all features: {len(all_features)} total")
            
            # Step 5: Create DataFrame with ONLY selected features (199 columns)
            df_features = pd.DataFrame(0, index=[0], columns=self.X_train_full.columns)
            
            # Fill with actual values
            for feature, value in all_features.items():
                if feature in df_features.columns:
                    df_features[feature] = value
            
            logger.info(f"DataFrame created with shape: {df_features.shape}")
            
            # Step 6: Apply scaling (no feature selection needed - already selected)
            if self.scaler is not None:
                selected_features = self.scaler.transform(df_features)
                logger.info(f"Scaled features shape: {selected_features.shape}")
            else:
                selected_features = df_features.values
                logger.warning("Scaler is None - using unscaled features")
            
            # Step 7: Make prediction
            probabilities = self.model.predict_proba(selected_features)[0]
            prediction = self.model.predict(selected_features)[0]
            predicted_class = self.label_encoder.inverse_transform([prediction])[0]
            
            # Step 8: Detect features for display
            detected_features = self._detect_features_improved(case_description)
            
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
    
    def _extract_traditional_features_improved(self, case_description: str) -> np.ndarray:
        """
        Extract traditional features matching improved model structure (49 features)
        
        Args:
            case_description: Text description of case
            
        Returns:
            Array of 49 traditional features in exact order from training data
        """
        # Get the exact column order from training data (non-BERT, non-TF-IDF)
        traditional_cols = [col for col in self.X_train_full.columns 
                         if not col.startswith('bert_') and not col.startswith('tfidf_')]
        
        # Initialize features with zeros
        features = pd.Series(0.0, index=traditional_cols)
        
        text = case_description.lower()
        
        # Text statistics
        if 'brief_facts_summary_length' in features.index:
            features['brief_facts_summary_length'] = len(text)
        if 'brief_facts_summary_word_count' in features.index:
            features['brief_facts_summary_word_count'] = len(text.split())
        if 'grounds_of_appeal_raw_text_summary_length' in features.index:
            features['grounds_of_appeal_raw_text_summary_length'] = len(text) * 0.4
        if 'grounds_of_appeal_raw_text_summary_word_count' in features.index:
            features['grounds_of_appeal_raw_text_summary_word_count'] = len(text.split()) * 0.4
        if 'court_of_appeal_analysis_summary_length' in features.index:
            features['court_of_appeal_analysis_summary_length'] = len(text) * 0.3
        if 'court_of_appeal_analysis_summary_word_count' in features.index:
            features['court_of_appeal_analysis_summary_word_count'] = len(text.split()) * 0.3
        
        # Grounds of appeal
        ground_keywords = {
            'gnd_contradictions': ['contradiction', 'inconsistent', 'conflicting'],
            'gnd_chain_of_custody': ['chain of custody', 'custody', 'preservation'],
            'gnd_illegal_search': ['illegal search', 'unlawful search', 'search raid'],
            'gnd_wrong_identification': ['identification', 'identify', 'mistaken identity'],
            'gnd_dying_declaration': ['dying declaration', 'deathbed statement'],
            'gnd_circumstantial': ['circumstantial', 'indirect evidence'],
            'gnd_medical_inconsistency': ['medical', 'jmo', 'post-mortem'],
            'gnd_misdirection': ['misdirection', 'wrong direction', 'legal error'],
            'gnd_procedural_error': ['procedural', 'procedure', 'process error'],
            'gnd_new_evidence': ['new evidence', 'fresh evidence'],
            'gnd_excessive_sentence': ['excessive', 'harsh', 'inadequate sentence'],
            'gnd_delay_prejudice': ['delay', 'prejudice', 'lapse of time'],
            'gnd_judicial_bias': ['bias', 'unfair', 'prejudiced judge']
        }
        
        for feature, keywords in ground_keywords.items():
            if feature in features.index:
                features[feature] = float(any(kw in text for kw in keywords))
        
        # Evidence presence
        evidence_keywords = {
            'eyewitness_present': ['eyewitness', 'witness', 'testimony'],
            'child_witness_present': ['child witness', 'minor witness'],
            'expert_evidence_present': ['expert', 'jmo', 'analyst', 'specialist'],
            'forensic_evidence_present': ['forensic', 'dna', 'fingerprint', 'ballistic'],
            'dying_declaration_present': ['dying declaration'],
            'confession_present': ['confession', 'admitted', 'dock statement'],
            'procedural_defects_present': ['procedural defect', 'process error', 'procedural'],
            'digital_evidence_present': ['cctv', 'phone', 'digital', 'video', 'recording'],
            'hospital_treatment_details_present': ['hospital', 'medical treatment', 'admitted to hospital']
        }
        
        for feature, keywords in evidence_keywords.items():
            if feature in features.index:
                features[feature] = float(any(kw in text for kw in keywords))
        
        # Medical evidence score
        if 'medical_evidence_score' in features.index:
            medical_terms = ['medical', 'jmo', 'post-mortem', 'autopsy', 'pathologist', 'medical evidence']
            features['medical_evidence_score'] = float(sum(1 for term in medical_terms if term in text))
        
        # Offence category (one-hot) - check exact column names
        offence_categories = [
            'offence_category_Assault_Violence',
            'offence_category_Customs', 
            'offence_category_Drug_Related',
            'offence_category_Environmental',
            'offence_category_Firearms_Weapons',
            'offence_category_Fraud_Corruption',
            'offence_category_Murder_Related',
            'offence_category_Other',
            'offence_category_Robbery_Theft',
            'offence_category_Sexual_Offenses',
            'offence_category_Traffic_Vehicle'
        ]
        
        offence_map = {
            'offence_category_Assault_Violence': ['assault', 'violence', 'harm'],
            'offence_category_Customs': ['customs', 'import', 'export'],
            'offence_category_Drug_Related': ['drug', 'narcotic', 'poisons', 'opium act', 'heroin'],
            'offence_category_Environmental': ['environment', 'wildlife', 'forest'],
            'offence_category_Firearms_Weapons': ['firearm', 'weapon', 'explosives'],
            'offence_category_Fraud_Corruption': ['fraud', 'corruption', 'bribery', 'cheating'],
            'offence_category_Murder_Related': ['murder', '296', 'homicide', 'culpable homicide'],
            'offence_category_Other': [],
            'offence_category_Robbery_Theft': ['robbery', 'theft', 'burglary', '380', '394'],
            'offence_category_Sexual_Offenses': ['rape', 'sexual', '363', '365', 'abuse'],
            'offence_category_Traffic_Vehicle': ['traffic', 'vehicle', 'rash driving']
        }
        
        # Initialize all offence categories to 0
        for category in offence_categories:
            if category in features.index:
                features[category] = 0.0
        
        # Set matching categories
        for category, keywords in offence_map.items():
            if category in features.index and keywords and any(kw in text for kw in keywords):
                features[category] = 1.0
        
        # Appeal type (one-hot) - check exact column names
        appeal_types = [
            'appeal_type_Both',
            'appeal_type_Conviction_Only',
            'appeal_type_Other',
            'appeal_type_Revision',
            'appeal_type_Sentence_Only',
            'appeal_type_Writ'
        ]
        
        appeal_map = {
            'appeal_type_Both': ['both', 'multiple'],
            'appeal_type_Conviction_Only': ['conviction', 'acquittal'],
            'appeal_type_Other': [],
            'appeal_type_Revision': ['revision', 'review'],
            'appeal_type_Sentence_Only': ['sentence', 'penalty', 'punishment'],
            'appeal_type_Writ': ['writ', 'certiorari', 'mandamus']
        }
        
        # Initialize all appeal types to 0
        for appeal_type in appeal_types:
            if appeal_type in features.index:
                features[appeal_type] = 0.0
        
        # Set matching types
        for appeal_type, keywords in appeal_map.items():
            if appeal_type in features.index and keywords and any(kw in text for kw in keywords):
                features[appeal_type] = 1.0
        
        # Temporal features
        if 'coa_year' in features.index:
            features['coa_year'] = 2024.0
        if 'appeal_duration_days' in features.index:
            features['appeal_duration_days'] = 730.0
        
        # Evidence count
        if 'evidence_count' in features.index:
            evidence_cols = [col for col in features.index if col.endswith('_present')]
            features['evidence_count'] = sum(features[col] for col in evidence_cols)
        
        # Convert to numpy array in correct order (should be 49 features)
        return features[traditional_cols].values.astype(float)
    
    def _detect_features_improved(self, case_description: str) -> Dict[str, List[str]]:
        """
        Detect and categorize active features for user display (improved version)
        
        Args:
            case_description: Text description of case
            
        Returns:
            Dictionary with detected features categorized
        """
        text = case_description.lower()
        
        detected = {
            'grounds': [],
            'evidence': [],
            'offence': [],
            'other': []
        }
        
        # Detect grounds
        ground_mapping = {
            'contradictions': ['contradiction', 'inconsistent', 'conflicting'],
            'chain of custody issues': ['chain of custody', 'custody', 'preservation'],
            'wrong identification': ['identification', 'identify', 'mistaken identity'],
            'dying declaration': ['dying declaration', 'deathbed statement'],
            'circumstantial evidence': ['circumstantial', 'indirect evidence'],
            'medical inconsistency': ['medical', 'jmo', 'post-mortem'],
            'misdirection': ['misdirection', 'wrong direction', 'legal error'],
            'procedural errors': ['procedural', 'procedure', 'process error'],
            'new evidence': ['new evidence', 'fresh evidence'],
            'excessive sentence': ['excessive', 'harsh', 'inadequate sentence'],
            'delay prejudice': ['delay', 'prejudice', 'lapse of time'],
            'judicial bias': ['bias', 'unfair', 'prejudiced judge']
        }
        
        for ground, keywords in ground_mapping.items():
            if any(kw in text for kw in keywords):
                detected['grounds'].append(ground.title())
        
        # Detect evidence
        evidence_mapping = {
            'eyewitness testimony': ['eyewitness', 'witness', 'testimony'],
            'expert evidence': ['expert', 'jmo', 'analyst', 'specialist'],
            'forensic evidence': ['forensic', 'dna', 'fingerprint', 'ballistic'],
            'confession': ['confession', 'admitted', 'dock statement'],
            'digital evidence': ['cctv', 'phone', 'digital', 'video', 'recording'],
            'medical treatment': ['hospital', 'medical treatment', 'admitted to hospital']
        }
        
        for evidence, keywords in evidence_mapping.items():
            if any(kw in text for kw in keywords):
                detected['evidence'].append(evidence.title())
        
        # Detect offence
        offence_mapping = {
            'Murder': ['murder', '296', 'homicide', 'culpable homicide'],
            'Sexual Offenses': ['rape', 'sexual', '363', '365', 'abuse'],
            'Drug Related': ['drug', 'narcotic', 'poisons', 'opium act', 'heroin'],
            'Robbery/Theft': ['robbery', 'theft', 'burglary', '380', '394'],
            'Fraud/Corruption': ['fraud', 'corruption', 'bribery', 'cheating']
        }
        
        for offence, keywords in offence_mapping.items():
            if any(kw in text for kw in keywords):
                detected['offence'].append(offence)
        
        # Detect other features
        if 'appeal' in text and 'allowed' in text:
            detected['other'].append('Appeal Allowed')
        if 'appeal' in text and 'dismissed' in text:
            detected['other'].append('Appeal Dismissed')
        if 'partly' in text:
            detected['other'].append('Partially Allowed')
        
        return detected

    def get_model_metadata(self) -> Dict[str, Any]:
        """
        Get model metadata information
        
        Returns:
            Dictionary with model metadata
        """
        try:
            # Try to load improved model metadata from JSON file in comp3 directory
            import os
            comp3_dir = os.path.dirname(os.path.dirname(self.model_path))
            metadata_path = os.path.join(comp3_dir, 'improved_model_metadata.json')
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Ensure required fields for schema
                required_fields = ['accuracy', 'model_name', 'training_date', 'training_samples', 'num_features']
                for field in required_fields:
                    if field not in metadata:
                        # Fallback to defaults if missing
                        defaults = {
                            'accuracy': 0.7975,
                            'model_name': 'Improved Calibrated Ensemble',
                            'training_date': '2026-03-01',
                            'training_samples': 1092,
                            'num_features': 199
                        }
                        metadata[field] = defaults.get(field)
                
                return metadata
            else:
                # Return improved model defaults
                return {
                    'accuracy': 0.7975,
                    'model_name': 'Improved Calibrated Ensemble',
                    'training_date': '2026-03-01',
                    'training_samples': 1092,
                    'num_features': 199
                }
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            # Return improved model defaults as fallback
            return {
                'accuracy': 0.7975,
                'model_name': 'Improved Calibrated Ensemble',
                'training_date': '2026-03-01',
                'training_samples': 1092,
                'num_features': 199
            }
