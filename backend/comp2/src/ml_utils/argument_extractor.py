"""
Argument Pattern Extraction Module
Uses trained models to extract argument patterns from similar cases
"""

import pickle
import numpy as np
import pandas as pd
import json
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ArgumentExtractor:
    """Extract argument patterns from similar cases using trained models"""
    
    def __init__(self, 
                 embeddings_path: str = "data/features/feature_vectors.pkl",
                 nn_model_path: str = "data/models/nearest_neighbors_model.pkl",
                 cases_csv_path: str = "data/processed/cleaned_cases.csv"):
        """
        Initialize argument extractor with trained models
        
        Args:
            embeddings_path: Path to pre-computed embeddings
            nn_model_path: Path to trained Nearest Neighbors model
            cases_csv_path: Path to cleaned cases CSV with metadata
        """
        self.embeddings = None
        self.case_ids = None
        self.nn_model = None
        self.cases_df = None
        self.case_dict = {}
        
        self._load_models(embeddings_path, nn_model_path, cases_csv_path)
    
    def _load_models(self, embeddings_path: str, nn_model_path: str, cases_csv_path: str):
        """Load trained models and data"""
        try:
            # Load embeddings
            with open(embeddings_path, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.case_ids = data['case_ids']
            logger.info(f"Loaded {len(self.case_ids)} case embeddings")
            
            # Load Nearest Neighbors model
            with open(nn_model_path, 'rb') as f:
                self.nn_model = pickle.load(f)
            logger.info("Loaded Nearest Neighbors model")
            
            # Load cases metadata
            if Path(cases_csv_path).exists():
                self.cases_df = pd.read_csv(cases_csv_path)
                # Create case dictionary for fast lookup
                for _, row in self.cases_df.iterrows():
                    case_id = row.get('case_id', '')
                    if case_id:
                        self.case_dict[case_id] = row.to_dict()
                logger.info(f"Loaded {len(self.case_dict)} case records")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def extract_argument_patterns(self, 
                                  query_embedding: np.ndarray,
                                  top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Extract argument patterns from similar cases using trained model
        
        Args:
            query_embedding: Embedding vector of the new case (1, 384)
            top_k: Number of similar cases to analyze
            
        Returns:
            List of dictionaries containing argument patterns from similar cases
        """
        if self.nn_model is None or self.embeddings is None:
            raise ValueError("Models not loaded. Initialize ArgumentExtractor first.")
        
        # Find similar cases using trained model
        n_neighbors = min(top_k, len(self.case_ids))
        distances, indices = self.nn_model.kneighbors(
            query_embedding, 
            n_neighbors=n_neighbors
        )
        
        argument_patterns = []
        
        for idx, distance in zip(indices[0], distances[0]):
            case_id = self.case_ids[idx]
            case_info = self.case_dict.get(case_id, {})
            
            # Extract argument patterns from this case
            patterns = self._extract_patterns_from_case(case_info, distance)
            if patterns:
                argument_patterns.extend(patterns)
        
        return argument_patterns
    
    def _extract_patterns_from_case(self, case_info: Dict, similarity_score: float) -> List[Dict]:
        """Extract argument patterns from a single case"""
        patterns = []
        
        if not case_info:
            return patterns
        
        # Get case text
        case_text = case_info.get('cleaned_text', case_info.get('full_text', ''))
        if not case_text or len(case_text) < 100:
            return patterns
        
        # Extract judge information
        judge_info = self._get_judge_info(case_info)
        
        # Extract legal principles mentioned
        legal_principles = self._extract_legal_principles(case_text)
        
        # Extract argument structure (prosecution/defense points)
        argument_points = self._extract_argument_points(case_text)
        
        # Determine perspective (prosecution/defense) based on case text
        perspective = self._determine_perspective(case_text)
        
        # Create argument pattern
        pattern = {
            "case_id": case_info.get('case_id', 'Unknown'),
            "year": case_info.get('year', 'Unknown'),
            "similarity_score": float(1 - similarity_score),  # Convert distance to similarity
            "perspective": perspective,
            "judge_names": judge_info.get("judge_names", []),
            "judge_statements": judge_info.get("key_statements", []),
            "legal_principles": legal_principles,
            "argument_points": argument_points,
            "case_excerpt": case_text[:500]  # First 500 chars for context
        }
        
        patterns.append(pattern)
        return patterns
    
    def _get_judge_info(self, case_info: Dict) -> Dict:
        """Extract judge information from case"""
        judge_info = {
            "judge_names": [],
            "key_statements": []
        }
        
        # Try to get judge info from JSON if available
        judge_info_json = case_info.get('judge_info_json', '{}')
        if judge_info_json and isinstance(judge_info_json, str):
            try:
                judge_data = json.loads(judge_info_json)
                judge_info["judge_names"] = judge_data.get("judge_names", [])
                
                # Get key holdings/statements
                holdings = judge_data.get("judge_holdings", [])
                statements = judge_data.get("judge_statements", [])
                
                # Combine and get top 3 most relevant
                all_statements = []
                for holding in holdings[:2]:
                    all_statements.append({
                        "judge": holding.get("judge_name", "Court"),
                        "statement": holding.get("holding", "")[:200]
                    })
                for stmt in statements[:2]:
                    all_statements.append({
                        "judge": stmt.get("judge_name", "Unknown"),
                        "statement": stmt.get("statement", "")[:200]
                    })
                
                judge_info["key_statements"] = all_statements[:3]
                
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract from judge_names column if available
        if not judge_info["judge_names"]:
            judge_names_str = case_info.get('judge_names', '')
            if judge_names_str:
                judge_info["judge_names"] = [name.strip() for name in str(judge_names_str).split(',') if name.strip()]
        
        return judge_info
    
    def _extract_legal_principles(self, text: str) -> List[str]:
        """Extract legal principles, sections, and statutes mentioned"""
        principles = []
        
        # Pattern 1: Section references (e.g., "Section 296", "Section 32(1)", "S. 300", "Ss. 296 and 300")
        section_pattern = r'(?:Section|S\.|Sections|Ss\.)\s+(\d+(?:\([a-z0-9]+\))?(?:\s+(?:and|&)\s+\d+(?:\([a-z0-9]+\))?)?(?:\s+of\s+(?:the\s+)?[A-Z][^,\.;\n]+)?)'
        sections = re.findall(section_pattern, text, re.IGNORECASE)
        principles.extend([f"Section {s}" if not s.lower().startswith('section') else s for s in sections[:8]])
        
        # Pattern 2: Act references (e.g., "Act No. 15 of 1979", "Penal Code", "Evidence Ordinance")
        act_pattern = r'(?:[A-Z][a-z]+\s+)*Act(?:\s+No\.?\s*\d+\s+of\s+\d{4})?|Penal\s+Code|Evidence\s+Ordinance|Criminal\s+Procedure\s+Code'
        acts = re.findall(act_pattern, text, re.IGNORECASE)
        principles.extend(acts[:5])
        
        # Pattern 3: Legal principles (common phrases)
        principle_patterns = [
            r'(?:principle|doctrine|rule)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:established|well-established)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+principle',
            r'(?:right\s+of\s+private\s+defence|burden\s+of\s+proof|reasonable\s+doubt|preponderance\s+of\s+evidence)',
        ]
        
        for pattern in principle_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, str):
                    principles.append(m.strip())
        
        # Clean up and deduplicate
        cleaned_principles = []
        seen = set()
        for p in principles:
            p_clean = re.sub(r'\s+', ' ', p).strip()
            if p_clean.lower() not in seen and len(p_clean) > 3:
                cleaned_principles.append(p_clean)
                seen.add(p_clean.lower())
        
        return cleaned_principles[:10]
    
    def _extract_argument_points(self, text: str) -> List[str]:
        """Extract key argument points from case text"""
        argument_points = []
        
        # Look for argument indicators with more flexible patterns
        # We use non-greedy matching to find the point up to a sentence ender
        argument_indicators = [
            # Prosecution/Defense/Court indicators
            r'(?:The\s+prosecution|Prosecution|State|Complainant|Respondent|The\s+defense|Defense|Defence|Accused|Appellant|Court|Judge|Magistrate)\s+(?:argues?|contends?|submits?|stated|submitted|contended|observed|held|decided|ruled|concluded)[\s:]+(.+?)(?:\.|;|\n)',
            # Counsel indicators
            r'(?:The\s+learned\s+)?Counsel\s+(?:for\s+the\s+)?(?:appellant|respondent|prosecution|defense|accused)\s+(?:argued|submitted|stated|contended)[\s:]+(.+?)(?:\.|;|\n)',
            # General submission indicators
            r'(?:It\s+is\s+|It\s+was\s+)(?:argued|contended|submitted|alleged|observed|held|found)\s+that\s+(.+?)(?:\.|;|\n)',
            # Claim indicators
            r'(?:The\s+main\s+ground\s+of\s+appeal|The\s+victim\s+had\s+said|The\s+accused\s+had\s+said)[\s:]+(.+?)(?:\.|;|\n)',
        ]
        
        seen_points = set()
        
        for pattern in argument_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                point = match.group(1).strip()
                # Clean up whitespace
                point = re.sub(r'\s+', ' ', point)
                
                # Check length and avoid duplicates
                if 25 < len(point) < 400:
                    if point.lower() not in seen_points:
                        argument_points.append(point)
                        seen_points.add(point.lower())
        
        # Take the most substantial points (longer ones) first
        argument_points.sort(key=len, reverse=True)
        return argument_points[:6]
    
    def _determine_perspective(self, text: str) -> str:
        """Determine if case supports prosecution or defense perspective"""
        text_lower = text.lower()
        
        # Prosecution indicators
        prosecution_keywords = [
            'convicted', 'guilty', 'prosecution proved', 'evidence establishes',
            'beyond reasonable doubt', 'offence committed', 'accused found guilty'
        ]
        
        # Defense indicators
        defense_keywords = [
            'acquitted', 'not guilty', 'defense succeeds', 'reasonable doubt',
            'evidence insufficient', 'prosecution failed', 'accused acquitted'
        ]
        
        prosecution_score = sum(1 for keyword in prosecution_keywords if keyword in text_lower)
        defense_score = sum(1 for keyword in defense_keywords if keyword in text_lower)
        
        if prosecution_score > defense_score:
            return "prosecution"
        elif defense_score > prosecution_score:
            return "defense"
        else:
            return "neutral"
    
    def format_patterns_for_llm(self, patterns: List[Dict]) -> str:
        """Format argument patterns for LLM context"""
        if not patterns:
            return ""
        
        formatted = "\n[MODEL-EXTRACTED ARGUMENT PATTERNS FROM SIMILAR CASES]:\n"
        
        for i, pattern in enumerate(patterns[:5], 1):  # Top 5 patterns
            formatted += f"\n[PATTERN {i}]:\n"
            formatted += f"Case: {pattern.get('case_id', 'Unknown')} ({pattern.get('year', 'Unknown')})\n"
            formatted += f"Similarity: {pattern.get('similarity_score', 0):.2f}\n"
            formatted += f"Perspective: {pattern.get('perspective', 'neutral')}\n"
            
            if pattern.get('judge_names'):
                formatted += f"Judges: {', '.join(pattern['judge_names'])}\n"
            
            if pattern.get('judge_statements'):
                formatted += "Key Judge Statements:\n"
                for stmt in pattern['judge_statements'][:2]:
                    judge = stmt.get('judge', 'Court')
                    text = stmt.get('statement', '')[:150]
                    formatted += f"  - {judge}: {text}...\n"
            
            if pattern.get('legal_principles'):
                formatted += f"Legal Principles: {', '.join(pattern['legal_principles'][:3])}\n"
            
            if pattern.get('argument_points'):
                formatted += "Argument Points:\n"
                for point in pattern['argument_points'][:2]:
                    formatted += f"  - {point[:150]}...\n"
        
        return formatted
