"""
Fixed version of the prediction method
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def predict_appeal_fixed(self, case_description: str) -> Dict[str, Any]:
    """
    Fixed prediction method following the demo approach
    """
    try:
        # Step 1: Generate TF-IDF features
        tfidf_dict = {}
        if self.tfidf_vectorizer is not None:
            tfidf_matrix = self.tfidf_vectorizer.transform([case_description])
            tfidf_array = tfidf_matrix.toarray()[0]
            tfidf_feature_names = [f'tfidf_{f}' for f in self.tfidf_vectorizer.get_feature_names_out()]
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
