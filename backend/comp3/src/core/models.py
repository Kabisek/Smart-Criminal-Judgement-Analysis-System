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

            # After loading cases, generate aggregated context statistics for
            # offence, location and year.
            self.context_stats = self._generate_context_stats(self.df_cases)

            # Generate aggregated statistics for grounds and evidence types.
            try:
                self.ground_stats, self.evidence_stats = self._generate_ground_evidence_stats(self.df_cases)
            except Exception as ge:
                logger.error(f"Error generating ground/evidence statistics: {ge}")
                self.ground_stats, self.evidence_stats = {}, {}
            
            logger.info("Data loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise

    def _generate_ground_evidence_stats(self, df: pd.DataFrame) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
        """
        Compute aggregated appeal outcome statistics for each ground of appeal and
        each evidence flag.
        """
        if 'result_category' not in df.columns:
            def simplify_outcome(val: str) -> str:
                if isinstance(val, str):
                    lower = val.lower()
                    if lower.startswith('dismissed'):
                        return 'Appeal_Dismissed'
                    elif lower.startswith('allowed'):
                        return 'Appeal_Allowed'
                    elif lower.startswith('partly'):
                        return 'Partly_Allowed'
                return 'Unknown'
            df = df.copy()
            df['result_category'] = df['combined_outcome'].apply(simplify_outcome)

        ground_stats: Dict[str, Dict[str, Any]] = {}
        evidence_stats: Dict[str, Dict[str, Any]] = {}

        ground_cols = [col for col in df.columns if col.startswith('gnd_')]
        evidence_cols = []
        for col in df.columns:
            if col.endswith('_present') and not col.startswith('gnd_'):
                evidence_cols.append(col)
        if 'confession_present' in df.columns and 'confession_present' not in evidence_cols:
            evidence_cols.append('confession_present')

        for col in ground_cols:
            subset = df[df[col].astype(str).str.lower() == 'yes']
            total = len(subset)
            if total == 0:
                continue
            counts = subset['result_category'].value_counts().to_dict()
            ground_stats[col] = {
                'count': total,
                'allowed_rate': round(counts.get('Appeal_Allowed', 0) / total, 3),
                'partly_rate': round(counts.get('Partly_Allowed', 0) / total, 3),
                'dismissed_rate': round(counts.get('Appeal_Dismissed', 0) / total, 3)
            }

        for col in evidence_cols:
            subset = df[(df[col].fillna(0) != 0) & (df[col].astype(str).str.lower() != 'no')]
            total = len(subset)
            if total == 0:
                continue
            counts = subset['result_category'].value_counts().to_dict()
            evidence_stats[col] = {
                'count': total,
                'allowed_rate': round(counts.get('Appeal_Allowed', 0) / total, 3),
                'partly_rate': round(counts.get('Partly_Allowed', 0) / total, 3),
                'dismissed_rate': round(counts.get('Appeal_Dismissed', 0) / total, 3)
            }

        return ground_stats, evidence_stats

    def compute_ground_analysis(self, detected_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given the detected grounds from a case description, return success
        statistics for each ground.
        """
        analysis: Dict[str, Any] = {}
        grounds = detected_features.get('grounds', [])
        for ground_name in grounds:
            base = ground_name.lower().replace(' ', '_')
            candidate_cols = [f'gnd_{base}']
            keywords = base.split('_')
            for col in self.ground_stats.keys():
                if all(kw in col for kw in keywords):
                    candidate_cols.append(col)
            for col in candidate_cols:
                if col in self.ground_stats:
                    analysis[ground_name] = self.ground_stats[col]
                    break
        return analysis

    def compute_evidence_analysis(self, detected_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given the detected evidence flags from a case description, return
        success statistics for each evidence type.
        """
        analysis: Dict[str, Any] = {}
        evidence_list = detected_features.get('evidence', [])
        for evidence_name in evidence_list:
            base = ''.join(ch for ch in evidence_name if ch.isalnum() or ch == ' ').lower().replace(' ', '_')
            candidate_cols = [f'{base}_present']
            if not base.endswith('present'):
                candidate_cols.append(f'{base}_evidence_present')
            keywords = base.split('_')
            for col in self.evidence_stats.keys():
                if all(kw in col for kw in keywords):
                    candidate_cols.append(col)
            for col in candidate_cols:
                if col in self.evidence_stats:
                    analysis[evidence_name] = self.evidence_stats[col]
                    break
        return analysis

    def _generate_context_stats(self, df: pd.DataFrame) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Generate aggregated statistics for offence groups, high court locations
        and appeal years.
        """
        df = df.copy()
        def simplify_outcome(val: str) -> str:
            if isinstance(val, str):
                lower = val.lower()
                if lower.startswith('dismissed'):
                    return 'Appeal_Dismissed'
                elif lower.startswith('allowed'):
                    return 'Appeal_Allowed'
                elif lower.startswith('partly'):
                    return 'Partly_Allowed'
            return 'Unknown'

        df['result_category'] = df['combined_outcome'].apply(simplify_outcome)
        try:
            self.df_cases['result_category'] = df['result_category']
        except Exception:
            pass

        def map_offence_group(offence: str) -> str:
            if not isinstance(offence, str):
                return 'Other'
            off = offence.lower()
            if any(word in off for word in ['murder', 'homicide']):
                return 'Murder_Related'
            if any(word in off for word in ['rape', 'sexual']):
                return 'Sexual_Offenses'
            if any(word in off for word in ['drug', 'heroin', 'narcotic']):
                return 'Drug_Related'
            if any(word in off for word in ['robbery', 'theft', 'burglary']):
                return 'Robbery_Theft'
            if any(word in off for word in ['fraud', 'corruption', 'bribery']):
                return 'Fraud_Corruption'
            return 'Other'

        df['offence_group'] = df['offence_category'].apply(map_offence_group)

        stats: Dict[str, Dict[str, Dict[str, Any]]] = {
            'offence': {},
            'location': {},
            'year': {}
        }

        offence_groups = df['offence_group'].unique()
        for group in offence_groups:
            subset = df[df['offence_group'] == group]
            counts = subset['result_category'].value_counts().to_dict()
            total = len(subset)
            if total > 0:
                stats['offence'][group] = {
                    'count': total,
                    'allowed_rate': round(counts.get('Appeal_Allowed', 0) / total, 3),
                    'partly_rate': round(counts.get('Partly_Allowed', 0) / total, 3),
                    'dismissed_rate': round(counts.get('Appeal_Dismissed', 0) / total, 3)
                }

        locations = df['high_court_location'].dropna().unique()
        for loc in locations:
            subset = df[df['high_court_location'] == loc]
            counts = subset['result_category'].value_counts().to_dict()
            total = len(subset)
            if total > 0:
                stats['location'][loc] = {
                    'count': total,
                    'allowed_rate': round(counts.get('Appeal_Allowed', 0) / total, 3),
                    'partly_rate': round(counts.get('Partly_Allowed', 0) / total, 3),
                    'dismissed_rate': round(counts.get('Appeal_Dismissed', 0) / total, 3)
                }

        years = df['coa_year'].dropna().unique()
        for year in years:
            subset = df[df['coa_year'] == year]
            counts = subset['result_category'].value_counts().to_dict()
            total = len(subset)
            if total > 0:
                stats['year'][int(year)] = {
                    'count': total,
                    'allowed_rate': round(counts.get('Appeal_Allowed', 0) / total, 3),
                    'partly_rate': round(counts.get('Partly_Allowed', 0) / total, 3),
                    'dismissed_rate': round(counts.get('Appeal_Dismissed', 0) / total, 3)
                }

        return stats

    def compute_context_analysis(self, detected_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute context-specific analytics for a case given its detected features.
        """
        context_stats = {}
        national_total = len(self.df_cases)
        national_counts = self.df_cases['result_category'].value_counts().to_dict()
        national_avg = {
            'count': national_total,
            'allowed_rate': round(national_counts.get('Appeal_Allowed', 0) / national_total, 3) if national_total else 0.0,
            'partly_rate': round(national_counts.get('Partly_Allowed', 0) / national_total, 3) if national_total else 0.0,
            'dismissed_rate': round(national_counts.get('Appeal_Dismissed', 0) / national_total, 3) if national_total else 0.0
        }

        offence_key = None
        offence_list = detected_features.get('offence', [])
        if offence_list:
            first = offence_list[0]
            key = first.replace(' ', '_')
            offence_key = key
        if offence_key and offence_key in self.context_stats['offence']:
            context_stats['offence'] = self.context_stats['offence'][offence_key]
        else:
            context_stats['offence'] = national_avg

        location = None
        if 'context' in detected_features and isinstance(detected_features['context'], dict):
            location = detected_features['context'].get('location')
        if location and location in self.context_stats['location']:
            context_stats['location'] = self.context_stats['location'][location]
        else:
            context_stats['location'] = national_avg

        year_val = None
        if 'context' in detected_features and isinstance(detected_features['context'], dict):
            year_val = detected_features['context'].get('year')
        if year_val and year_val in self.context_stats['year']:
            context_stats['year'] = self.context_stats['year'][year_val]
        else:
            context_stats['year'] = national_avg

        return context_stats

    def _build_feature_dataframe(self, case_description: str) -> pd.DataFrame:
        """
        Build the full feature DataFrame for a case description.
        Used internally by both predict_appeal and find_similar_cases.

        Args:
            case_description: Detailed case description text

        Returns:
            DataFrame with shape (1, n_train_features) ready for model input
        """
        # Generate TF-IDF features
        tfidf_dict = {}
        if self.tfidf_vectorizer is not None:
            tfidf_matrix = self.tfidf_vectorizer.transform([case_description])
            tfidf_array = tfidf_matrix.toarray()[0]
            tfidf_feature_names = [f'tfidf_{feature}' for feature in self.tfidf_vectorizer.get_feature_names_out()]
            tfidf_dict = dict(zip(tfidf_feature_names, tfidf_array))

        # Generate BERT embedding
        bert_features = self.bert_processor.get_embedding(case_description)
        bert_dict = {f'bert_{i}': val for i, val in enumerate(bert_features)}

        # Extract traditional features
        traditional_dict = {}
        traditional_cols = [col for col in self.X_train_full.columns
                            if not col.startswith('bert_') and not col.startswith('tfidf_')]
        text = case_description.lower()

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

        # Combine all features
        all_features = {**traditional_dict, **tfidf_dict, **bert_dict}

        # Create DataFrame aligned to training columns
        df_features = pd.DataFrame(0, index=[0], columns=self.X_train_full.columns)
        for feature, value in all_features.items():
            if feature in df_features.columns:
                df_features[feature] = value

        return df_features

    def predict_appeal(self, case_description: str) -> Dict[str, Any]:
        """
        Predict appeal outcome for a given case description
        
        Args:
            case_description: Detailed case description
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Step 1-4: Build full feature DataFrame (shared helper)
            df_features = self._build_feature_dataframe(case_description)
            logger.info(f"DataFrame created with shape: {df_features.shape}")

            # Step 5: Re-extract BERT embedding for similarity search
            bert_features = self.bert_processor.get_embedding(case_description)

            # Step 6: Apply scaling
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

            # Step 9: Compute context analysis using aggregated statistics
            try:
                context_analysis = self.compute_context_analysis(detected_features)
            except Exception as context_e:
                logger.error(f"Error computing context analysis: {context_e}")
                context_analysis = {}

            # Step 10: Compute additional analytics for grounds and evidence
            try:
                grounds_analysis = self.compute_ground_analysis(detected_features)
            except Exception as ge:
                logger.error(f"Error computing grounds analysis: {ge}")
                grounds_analysis = {}

            try:
                evidence_analysis = self.compute_evidence_analysis(detected_features)
            except Exception as ee:
                logger.error(f"Error computing evidence analysis: {ee}")
                evidence_analysis = {}

            # Create result dictionary with analytics
            result = {
                'probabilities': {
                    'Appeal_Allowed': float(probabilities[0] * 100),
                    'Appeal_Dismissed': float(probabilities[1] * 100),
                    'Partly_Allowed': float(probabilities[2] * 100)
                },
                'prediction': predicted_class,
                'confidence': float(max(probabilities) * 100),
                'bert_embedding': bert_features,
                'detected_features': detected_features,
                'context_analysis': context_analysis,
                'grounds_analysis': grounds_analysis,
                'evidence_analysis': evidence_analysis
            }

            # Step 11: Find similar cases using enhanced similarity
            try:
                similar_cases = self.find_similar_cases(case_description, bert_features)
                result['similar_cases'] = similar_cases
            except Exception as sc_e:
                logger.error(f"Error finding similar cases: {sc_e}")
                result['similar_cases'] = []

            return result
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            raise
        
    def find_similar_cases(self, case_description: str, bert_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Enhanced similar cases search using 4 features + prediction outcome
        
        Args:
            case_description: Full case description text
            bert_embedding: BERT embedding of current case
            top_k: Number of similar cases to return
            
        Returns:
            List of similar cases with enhanced similarity scores
        """
        try:
            # 1. Extract user features
            user_features = self._detect_features_improved(case_description)

            # FIX: Use _build_feature_dataframe instead of the missing
            # _extract_traditional_features_improved method
            df_user = self._build_feature_dataframe(case_description)
            if self.scaler is not None:
                scaled_user = self.scaler.transform(df_user)
            else:
                scaled_user = df_user.values

            user_prediction_numeric = self.model.predict(scaled_user)[0]
            user_prediction = self.label_encoder.inverse_transform([user_prediction_numeric])[0]

            # 2. Calculate BERT similarity
            bert_similarities = cosine_similarity(
                bert_embedding.reshape(1, -1),
                self.train_embeddings
            )[0]
                     
            # 3. Calculate enhanced similarities for each training case
            enhanced_similarities = []
            
            for idx in range(len(self.train_embeddings)):
                train_case_text = self.df_cases.iloc[idx].get('brief_facts_summary', '')
                train_features = self._detect_features_improved(str(train_case_text))
                train_prediction = self.label_encoder.inverse_transform([self.y_train[idx]])[0]
                
                bert_sim = bert_similarities[idx]
                
                grounds_sim = self._jaccard_similarity(
                    set(user_features.get('grounds', [])),
                    set(train_features.get('grounds', []))
                )
                
                evidence_sim = self._jaccard_similarity(
                    set(user_features.get('evidence', [])),
                    set(train_features.get('evidence', []))
                )
                
                offence_sim = self._jaccard_similarity(
                    set(user_features.get('offence', [])),
                    set(train_features.get('offence', []))
                )
                
                prediction_match = 1.0 if user_prediction == train_prediction else 0.0
                
                # Weighted combination
                final_score = (
                    0.2 * bert_sim +
                    0.2 * grounds_sim +
                    0.2 * evidence_sim +
                    0.2 * offence_sim +
                    0.2 * prediction_match
                )
                
                enhanced_similarities.append((idx, final_score))
            
            # 4. Get top k most similar cases
            enhanced_similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, score in enhanced_similarities[:top_k]]
            
            # 5. Build similar cases list
            # 5. Build similar cases list
            similar_cases = []
            for idx in top_indices:
                case = self.df_cases.iloc[idx]
                outcome = self.label_encoder.inverse_transform([self.y_train[idx]])[0]
                similarity_score = enhanced_similarities[top_indices.index(idx)][1] * 100
                
                # Extract all case data with proper error handling
                try:
                    case_facts = str(case['brief_facts_summary']) if pd.notna(case['brief_facts_summary']) else 'Details not available'
                except:
                    case_facts = 'Details not available'
                    
                try:
                    conviction_status = str(case['coa_conviction_status']) if pd.notna(case['coa_conviction_status']) else 'Not specified'
                except:
                    conviction_status = 'Not specified'
                    
                try:
                    case_number = str(case['court_of_appeal_case_no']) if pd.notna(case['court_of_appeal_case_no']) else f"Case_{idx}"
                except:
                    case_number = f"Case_{idx}"
                    
                try:
                    offence = str(case['offence_category']) if pd.notna(case['offence_category']) else 'Not specified'
                except:
                    offence = 'Not specified'
                    
                try:
                    high_court = str(case['high_court_location']) if pd.notna(case['high_court_location']) else 'Not specified'
                except:
                    high_court = 'Not specified'
                    
                try:
                    grounds = str(case['grounds_of_appeal_raw_text_summary']) if pd.notna(case['grounds_of_appeal_raw_text_summary']) else 'Not specified'
                except:
                    grounds = 'Not specified'
                
                # NEW FIELDS - DECISION DATE
                try:
                    judgment_date = str(case['judgment_date_coa']) if pd.notna(case['judgment_date_coa']) else None
                    # Format as YYYY-MM-DD if it's a date string
                    if judgment_date and judgment_date != 'NaT':
                        decision_date = judgment_date.split(' ')[0] if ' ' in judgment_date else judgment_date
                    else:
                        decision_date = None
                except:
                    decision_date = None
                
                # NEW FIELDS - VERDICT REASONING (Court of Appeal Analysis)
                try:
                    verdict_reasoning = str(case['court_of_appeal_analysis_summary']) if pd.notna(case['court_of_appeal_analysis_summary']) else None
                    if verdict_reasoning == 'nan':
                        verdict_reasoning = None
                except:
                    verdict_reasoning = None
                
                # NEW FIELDS - JUDGE'S COMMENTARY (High Court Analysis)
                try:
                    judge_commentary = str(case['hc_analysis_summary']) if pd.notna(case['hc_analysis_summary']) else None
                    if judge_commentary == 'nan':
                        judge_commentary = None
                except:
                    judge_commentary = None
                
                # NEW FIELDS - APPEAL GROUNDS LIST (Parse from structured notes)
                try:
                    appeal_grounds_list = []
                    if pd.notna(case['grounds_of_appeal_structured_notes']) and case['grounds_of_appeal_structured_notes'] != 'nan':
                        structured = str(case['grounds_of_appeal_structured_notes'])
                        # Split by common delimiters
                        appeal_grounds_list = [g.strip() for g in structured.split(',') if g.strip()]
                    
                    if not appeal_grounds_list:  # Fallback to extracted features
                        appeal_grounds_list = train_features.get('grounds', [])
                except:
                    appeal_grounds_list = train_features.get('grounds', [])
                
                # NEW FIELDS - EVIDENCE TYPES LIST
                try:
                    evidence_types = []
                    evidence_primary = str(case['evidence_type_primary']) if pd.notna(case['evidence_type_primary']) else ''
                    evidence_secondary = str(case['evidence_type_secondary']) if pd.notna(case['evidence_type_secondary']) else ''
                    
                    if evidence_primary and evidence_primary != 'nan':
                        evidence_types.extend([e.strip() for e in evidence_primary.split(',') if e.strip()])
                    if evidence_secondary and evidence_secondary != 'nan':
                        evidence_types.extend([e.strip() for e in evidence_secondary.split(',') if e.strip()])
                    
                    # Remove duplicates while preserving order
                    evidence_types = list(dict.fromkeys(evidence_types))
                    
                    if not evidence_types:
                        evidence_types = train_features.get('evidence', [])
                except:
                    evidence_types = train_features.get('evidence', [])
                
                # NEW FIELDS - APPEAL SUCCESS RATE (from statistics)
                try:
                    appeal_success_rate = None
                    # Look up ground success rate from ground_stats
                    if appeal_grounds_list and self.ground_stats:
                        ground_col = f"gnd_{appeal_grounds_list[0].lower().replace(' ', '_')}"
                        if ground_col in self.ground_stats:
                            appeal_success_rate = self.ground_stats[ground_col].get('allowed_rate', None)
                except:
                    appeal_success_rate = None
                
                # NEW FIELDS - PRECEDENT VALUE
                try:
                    precedent_value = None
                    precedents_cited = str(case['precedents_cited_list']) if pd.notna(case['precedents_cited_list']) else None
                    if precedents_cited and precedents_cited != 'nan' and len(precedents_cited) > 5:
                        precedent_value = "High - Multiple precedents cited"
                    else:
                        precedent_value = "Standard - Reference precedent"
                except:
                    precedent_value = None
                
                # NEW FIELDS - EXTRACT YEAR FROM DECISION DATE
                try:
                    year = None
                    if decision_date:
                        year = int(decision_date.split('-')[0])
                    elif 'coa_year' in case.index:
                        year = int(case['coa_year']) if pd.notna(case['coa_year']) else None
                except:
                    year = None
                
                similar_cases.append({
                    'case_id': case_number,
                    'similarity': similarity_score,
                    'outcome': outcome,
                    'conviction_status': conviction_status,
                    'facts': case_facts,
                    'offence': offence,
                    'high_court': high_court,
                    'grounds': grounds,
                    # NEW FIELDS
                    'decision_date': decision_date,
                    'verdict_reasoning': verdict_reasoning,
                    'judge_commentary': judge_commentary,
                    'appeal_grounds_list': appeal_grounds_list,
                    'evidence_types': evidence_types,
                    'appeal_success_rate': appeal_success_rate,
                    'precedent_value': precedent_value,
                    'year': year,
                    'citation': case_number  # Use case_number as citation
                })

            return similar_cases
            
        except Exception as e:
            logger.error(f"Error in enhanced similarity search: {e}")
            raise

    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Calculate Jaccard similarity between two sets"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

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