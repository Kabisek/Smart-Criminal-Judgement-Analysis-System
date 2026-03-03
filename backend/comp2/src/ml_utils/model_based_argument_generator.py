"""
Model-Based Argument Generator
Generates arguments using trained models only (no LLM)
"""

import numpy as np
import pandas as pd
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelBasedArgumentGenerator:
    """Generate arguments using only trained models (no LLM)"""
    
    def __init__(self, argument_extractor):
        """
        Initialize model-based argument generator
        
        Args:
            argument_extractor: ArgumentExtractor instance with loaded models
        """
        self.argument_extractor = argument_extractor
        logger.info("✅ Model-based argument generator initialized (no LLM)")
    
    def generate_arguments_from_patterns(self, 
                                        model_patterns: List[Dict],
                                        case_text: str,
                                        similar_cases: List[Dict],
                                        case_ids: List[str]) -> List[Dict]:
        """
        Generate arguments directly from model-extracted patterns
        
        Args:
            model_patterns: Argument patterns extracted from similar cases
            case_text: Text of the new case
            similar_cases: List of similar case dictionaries
            case_ids: List of case IDs
            
        Returns:
            List of argument dictionaries
        """
        if not model_patterns:
            logger.warning("No model patterns provided, generating from similar cases only")
            return self._generate_from_similar_cases(similar_cases, case_ids)
        
        arguments = []
        
        # Group patterns by perspective
        prosecution_patterns = [p for p in model_patterns if p.get('perspective') == 'prosecution']
        defense_patterns = [p for p in model_patterns if p.get('perspective') == 'defense']
        neutral_patterns = [p for p in model_patterns if p.get('perspective') == 'neutral']
        
        # Generate prosecution argument
        if prosecution_patterns:
            arg = self._build_argument_from_patterns(
                prosecution_patterns,
                "Precedent Support - Prosecution",
                "prosecution",
                case_ids
            )
            arguments.append(arg)
        
        # Generate defense argument
        if defense_patterns:
            arg = self._build_argument_from_patterns(
                defense_patterns,
                "Precedent Support - Defense",
                "defense",
                case_ids
            )
            arguments.append(arg)
        
        # Generate mitigating argument (from neutral or defense patterns)
        mitigating_patterns = neutral_patterns + defense_patterns[:2]
        if mitigating_patterns:
            arg = self._build_argument_from_patterns(
                mitigating_patterns,
                "Precedent Support - Mitigating",
                "mitigating",
                case_ids
            )
            arguments.append(arg)
        
        # Generate aggressive argument (from prosecution patterns)
        if prosecution_patterns:
            arg = self._build_argument_from_patterns(
                prosecution_patterns[:2],  # Top 2 most similar
                "Precedent Support - Aggressive",
                "aggressive",
                case_ids
            )
            arguments.append(arg)
        
        # Ensure we have at least 4 arguments
        while len(arguments) < 4:
            # Use any available patterns
            remaining_patterns = [p for p in model_patterns if p not in [a.get('_source_patterns', []) for a in arguments]]
            if remaining_patterns:
                perspective = remaining_patterns[0].get('perspective', 'neutral')
                arg = self._build_argument_from_patterns(
                    [remaining_patterns[0]],
                    f"Precedent Support - {perspective.title()}",
                    perspective,
                    case_ids
                )
                arguments.append(arg)
            else:
                break
        
        logger.info(f"✅ Generated {len(arguments)} arguments from model patterns")
        return arguments
    
    def _build_argument_from_patterns(self,
                                     patterns: List[Dict],
                                     title: str,
                                     perspective: str,
                                     case_ids: List[str]) -> Dict:
        """Build a single argument from patterns"""
        
        # Collect information from patterns
        supporting_cases = []
        judge_names = []
        judge_statements = []
        legal_principles = []
        argument_points = []
        
        for pattern in patterns[:3]:  # Top 3 patterns
            case_id = pattern.get('case_id')
            if case_id:
                supporting_cases.append(case_id)
            
            # Collect judge names
            pattern_judges = pattern.get('judge_names', [])
            if isinstance(pattern_judges, list):
                judge_names.extend([j for j in pattern_judges if j and j not in judge_names])
            elif isinstance(pattern_judges, str):
                # Parse comma-separated string
                names = [n.strip() for n in pattern_judges.split(',') if n.strip()]
                judge_names.extend([n for n in names if n not in judge_names])
            
            # Collect judge statements
            pattern_statements = pattern.get('judge_statements', [])
            for stmt in pattern_statements:
                if isinstance(stmt, dict):
                    stmt_text = stmt.get('statement', '')
                    if stmt_text and stmt_text not in judge_statements:
                        judge_statements.append(stmt_text[:200])
                elif isinstance(stmt, str) and stmt not in judge_statements:
                    judge_statements.append(stmt[:200])
            
            # Collect legal principles
            pattern_principles = pattern.get('legal_principles', [])
            for principle in pattern_principles:
                if principle and principle not in legal_principles:
                    legal_principles.append(principle)
            
            # Collect argument points
            pattern_points = pattern.get('argument_points', [])
            for point in pattern_points:
                if point and point not in argument_points:
                    argument_points.append(point)
        
        # Build content from collected information
        content_parts = []
        
        # Start with case citations
        if supporting_cases:
            case_refs = ', '.join(supporting_cases[:3])
            content_parts.append(f"In similar cases {case_refs}, the courts have established relevant precedents.")
        
        # Add judge statements
        if judge_statements:
            content_parts.append(f"Judges including {', '.join(judge_names[:3]) if judge_names else 'the court'} have held: '{judge_statements[0]}'")
        
        # Add legal principles
        if legal_principles:
            content_parts.append(f"These cases reference {', '.join(legal_principles[:2])}, which are relevant to the current matter.")
        
        # Add argument points
        if argument_points:
            content_parts.append(f"Key points from these precedents include: {argument_points[0]}")
        
        # Combine into content
        content = " ".join(content_parts) if content_parts else f"This argument is supported by {len(patterns)} similar case patterns."
        
        # Calculate similarity-based strength score
        avg_similarity = np.mean([p.get('similarity_score', 0.5) for p in patterns])
        strength_score = min(0.9, 0.5 + avg_similarity * 0.4)  # Scale similarity to 0.5-0.9
        
        argument = {
            "title": title,
            "content": content,
            "perspective": perspective,
            "strength_score": round(strength_score, 2),
            "supporting_cases": supporting_cases[:5],
            "judge_names": judge_names[:5],
            "judge_statements": judge_statements[:5],
            "legal_principles": legal_principles[:5],
            "penal_codes": [],
            "argument_points": argument_points[:10],       # New clear naming
            "model_extracted_points": argument_points[:10],  # Keep for backward compatibility
            "_source_patterns": patterns  # Store for reference
        }
        
        return argument
    
    def _generate_from_similar_cases(self, similar_cases: List[Dict], case_ids: List[str]) -> List[Dict]:
        """Fallback: Generate arguments from similar cases when no patterns available"""
        arguments = []
        
        for i, (case_id, case_info) in enumerate(zip(case_ids[:4], similar_cases[:4])):
            perspective = "prosecution" if i < 2 else "defense"
            title = f"Precedent Support - {perspective.title()}"
            
            # Extract basic info
            text = case_info.get('cleaned_text', case_info.get('full_text', ''))[:500] if isinstance(case_info, dict) else str(case_info)[:500]
            year = case_info.get('year', 'Unknown') if isinstance(case_info, dict) else 'Unknown'
            
            argument = {
                "title": title,
                "content": f"Case {case_id} ({year}) provides relevant precedent: {text}...",
                "perspective": perspective,
                "strength_score": 0.6,
                "supporting_cases": [case_id],
                "judge_names": [],
                "judge_statements": [],
                "legal_principles": [],
                "penal_codes": [],
                "argument_points": [],
                "model_extracted_points": []
            }
            arguments.append(argument)
        
        return arguments
