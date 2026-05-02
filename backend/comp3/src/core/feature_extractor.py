"""
Feature extractor for traditional legal features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extracts traditional features from legal case descriptions"""
    
    def __init__(self):
        """Initialize feature extractor with keyword mappings"""
        
        # Grounds of appeal keywords
        self.ground_keywords = {
            'gnd_contradictions': ['contradiction', 'inconsistent', 'conflicting'],
            'gnd_chain_of_custody': ['chain of custody', 'custody', 'preservation'],
            'gnd_wrong_identification': ['identification', 'identify', 'mistaken identity'],
            'gnd_medical_inconsistency': ['medical', 'jmo', 'post-mortem'],
            'gnd_misdirection_on_law': ['misdirection', 'wrong direction'],
            'gnd_procedural_error': ['procedural', 'procedure', 'process'],
            'gnd_illegal_search_or_raid': ['illegal search', 'unlawful search'],
            'gnd_dying_declaration_validity': ['dying declaration'],
            'gnd_circumstantial_insufficient': ['circumstantial', 'indirect evidence'],
            'gnd_new_evidence': ['new evidence', 'fresh evidence'],
            'gnd_sentence_excessive_or_inadequate': ['excessive', 'harsh', 'inadequate'],
            'gnd_delay_prejudice': ['delay', 'prejudice'],
            'gnd_judicial_bias_or_unfair_trial': ['bias', 'unfair'],
        }
        
        # Evidence keywords
        self.evidence_keywords = {
            'eyewitness_present': ['eyewitness', 'witness', 'testimony'],
            'expert_evidence_present': ['expert', 'jmo', 'analyst'],
            'forensic_evidence_present': ['forensic', 'dna', 'fingerprint'],
            'confession_present': ['confession', 'admitted'],
            'dying_declaration_present': ['dying declaration'],
            'digital_evidence_present': ['cctv', 'phone', 'digital'],
            'child_witness_present': ['child witness', 'minor witness'],
            'procedural_defects_present': ['procedural defect'],
            'hospital_treatment_details_present': ['hospital', 'medical treatment'],
        }
        
        # Offence category keywords
        self.offence_map = {
            'offence_category_grouped_Murder_Related': ['murder', '296', 'homicide'],
            'offence_category_grouped_Sexual_Offenses': ['rape', 'sexual', '363'],
            'offence_category_grouped_Drug_Related': ['drug', 'narcotic', 'heroin'],
            'offence_category_grouped_Robbery_Theft': ['robbery', 'theft', 'burglary'],
            'offence_category_grouped_Fraud_Corruption': ['fraud', 'corruption', 'bribery'],
        }

        # Approximate mapping for high court locations. This mapping is used
        # to detect a location from the case description when present. The keys
        # correspond to the canonical `high_court_location` values in the
        # dataset. Feel free to add more as necessary.
        self.location_keywords = {
            'Colombo': ['colombo'],
            'Matara': ['matara'],
            'Puttalam': ['puttalam', 'puttlam'],
            'Chilaw': ['chilaw'],
            'Kurunegala': ['kurunegala'],
            'Gampaha': ['gampaha'],
            'Kalutara': ['kalutara'],
            'Balapitiya': ['balapitiya'],
            'Panadura': ['panadura'],
            'Embilipitiya': ['embilipitiya'],
            'Kandy': ['kandy'],
            'Monaragala': ['monaragala'],
            'Negombo': ['negombo'],
            'Jaffna': ['jaffna'],
            'Anuradhapura': ['anuradhapura'],
            'Rathnapura': ['rathnapura', 'ratnapura'],
            'Galle': ['galle'],
            'Homagama': ['homagama'],
            'Hambantota': ['hambantota'],
            'Vavuniya': ['vavuniya']
        }

    def extract_case_context(self, text: str) -> Dict[str, Any]:
        """
        Extract simple contextual information (year and location) from the case description.

        The year is inferred from patterns like "/2020" in case numbers or explicit dates.
        The location is inferred by matching known keywords to high court locations.

        Args:
            text: Lowercased case description

        Returns:
            Dictionary with optional keys 'year' and 'location'
        """
        import re
        context: Dict[str, Any] = {}
        # Attempt to find a 4-digit year following a slash (e.g. "HC/567/2023")
        match = re.search(r"/[0-9]{4}", text)
        if match:
            try:
                context['year'] = int(match.group(0).strip('/'))
            except Exception:
                pass
        # Match location keywords
        for loc, kws in self.location_keywords.items():
            if any(kw in text for kw in kws):
                context['location'] = loc
                break
        return context
    
    def extract_features_from_text(self, case_description: str, feature_columns: List[str]) -> np.ndarray:
        """
        Extract 59 traditional features from case description
        
        Args:
            case_description: Text description of the case
            feature_columns: List of expected feature column names
            
        Returns:
            Array of extracted features
        """
        # Get non-BERT columns (first 59 features)
        non_bert_cols = feature_columns[:59]
        features = pd.Series(0.0, index=non_bert_cols)
        
        text = case_description.lower()
        words = text.split()
        
        # Text length features
        if 'brief_facts_summary_length' in features.index:
            features['brief_facts_summary_length'] = len(text)
        if 'brief_facts_summary_word_count' in features.index:
            features['brief_facts_summary_word_count'] = len(words)
        
        # Extract grounds of appeal features
        for feature, keywords in self.ground_keywords.items():
            if feature in features.index:
                features[feature] = float(any(kw in text for kw in keywords))
        
        # Extract evidence features
        for feature, keywords in self.evidence_keywords.items():
            if feature in features.index:
                features[feature] = float(any(kw in text for kw in keywords))
        
        # Extract offence features
        for feature, keywords in self.offence_map.items():
            if feature in features.index:
                features[feature] = float(any(kw in text for kw in keywords))
        
        return features.values
    
    def detect_active_features(self, case_description: str, feature_columns: List[str]) -> Dict[str, List[str]]:
        """
        Detect and categorize active features for user display
        
        Args:
            case_description: Text description of the case
            feature_columns: List of feature column names
            
        Returns:
            Dictionary with categorized detected features
        """
        traditional_features = self.extract_features_from_text(case_description, feature_columns)
        non_bert_cols = feature_columns[:59]
        
        detected_features = {
            'grounds': [],
            'evidence': [],
            'offence': [],
            'other': []
        }
        
        for i, (col, val) in enumerate(zip(non_bert_cols, traditional_features)):
            if val > 0.5:  # Feature is "active"
                if col.startswith('gnd_'):
                    detected_features['grounds'].append(col.replace('gnd_', '').replace('_', ' ').title())
                elif '_present' in col:
                    detected_features['evidence'].append(col.replace('_present', '').replace('_', ' ').title())
                elif 'offence_category' in col:
                    detected_features['offence'].append(col.split('_')[-1].replace('_', ' ').title())
                elif col not in ['brief_facts_summary_length', 'brief_facts_summary_word_count', 
                               'grounds_of_appeal_raw_text_summary_length', 'grounds_of_appeal_raw_text_summary_word_count',
                               'court_of_appeal_analysis_summary_length', 'court_of_appeal_analysis_summary_word_count',
                               'coa_year', 'appeal_duration_days']:
                    detected_features['other'].append(col.replace('_', ' ').title())
        
        # Also attach context information (year, location) for downstream analytics
        context_info = self.extract_case_context(case_description.lower())
        if context_info:
            detected_features['context'] = context_info
        return detected_features
