"""
Judge Information Extraction Module
Extracts judge names and their statements/holdings from legal judgments
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class JudgeExtractor:
    """Extract judge names and statements from legal documents"""
    
    def __init__(self):
        # Common judge title patterns in Sri Lankan courts
        self.judge_titles = [
            r'Hon\.?\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)\s*Justice',
            r'Hon\.?\s*Justice',
            r'Justice\s+(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)',
            r'Judge\s+(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)',
            r'Presiding\s+Judge',
            r'Chief\s+Justice',
            r'President\s+of\s+the\s+Court'
        ]
        
        # Patterns for identifying judge statements
        self.statement_patterns = [
            r'(?:I|We)\s+(?:hold|find|conclude|determine|decide|rule|observe|note)',
            r'(?:In\s+my|In\s+our)\s+(?:view|opinion|judgment)',
            r'(?:It\s+is|This\s+is)\s+(?:held|found|concluded|determined)',
            r'(?:Court|This\s+Court)\s+(?:holds|finds|concludes|determines)',
            r'(?:Accordingly|Therefore|Hence|Thus)',
        ]
        
    def extract_judge_info(self, text: str) -> Dict:
        """
        Extract judge names and their statements from legal text
        
        Args:
            text: Legal judgment text
            
        Returns:
            dict: Contains judge_names, judge_statements, and metadata
        """
        result = {
            "judge_names": [],
            "judge_statements": [],
            "judge_holdings": [],
            "has_judge_info": False
        }
        
        try:
            # Extract judge names
            judge_names = self._extract_judge_names(text)
            result["judge_names"] = judge_names
            
            # Extract judge statements
            if judge_names:
                statements = self._extract_judge_statements(text, judge_names)
                result["judge_statements"] = statements
                
                # Extract holdings (key legal conclusions)
                holdings = self._extract_holdings(text, judge_names)
                result["judge_holdings"] = holdings
                
                result["has_judge_info"] = True
                
        except Exception as e:
            logger.warning(f"Error extracting judge info: {e}")
            
        return result
    
    def _extract_judge_names(self, text: str) -> List[str]:
        """Extract judge names from text"""
        judge_names = []
        seen_names = set()
        
        # Pattern 1: Look for judge titles followed by names
        for title_pattern in self.judge_titles:
            # Pattern: "Hon. Justice [Name]" or "Justice [Name]"
            pattern = rf'{title_pattern}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                name = match.group(1).strip()
                if name and len(name) > 2 and name not in seen_names:
                    # Filter out common false positives
                    if not any(word in name.lower() for word in ['court', 'appeal', 'judgment', 'case']):
                        judge_names.append(name)
                        seen_names.add(name)
        
        # Pattern 2: Look for "J." abbreviation followed by name (e.g., "J. Fernando")
        pattern = r'\b([A-Z]\.\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            name = match.group(1).strip()
            if name and name not in seen_names:
                judge_names.append(name)
                seen_names.add(name)
        
        # Pattern 3: Look for names in signature lines or judgment headers
        # Common format: "Before: [Judge Name]" or "Delivered by: [Judge Name]"
        signature_patterns = [
            r'Before[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Delivered\s+by[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Written\s+by[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in signature_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if name and name not in seen_names:
                    judge_names.append(name)
                    seen_names.add(name)
        
        return list(set(judge_names))  # Remove duplicates
    
    def _extract_judge_statements(self, text: str, judge_names: List[str]) -> List[Dict]:
        """Extract statements made by judges"""
        statements = []
        
        if not judge_names:
            return statements
        
        # Split text into sentences
        sentences = re.split(r'[.!?]+\s+', text)
        
        for sentence in sentences:
            # Check if sentence contains judge statement patterns
            has_statement_pattern = any(
                re.search(pattern, sentence, re.IGNORECASE) 
                for pattern in self.statement_patterns
            )
            
            # Check if sentence mentions a judge name
            has_judge_name = any(
                name.lower() in sentence.lower() 
                for name in judge_names
            )
            
            if has_statement_pattern or has_judge_name:
                # Try to identify which judge made the statement
                judge_name = None
                for name in judge_names:
                    if name.lower() in sentence.lower():
                        judge_name = name
                        break
                
                # Extract key legal points (look for section references, legal terms)
                legal_terms = re.findall(
                    r'(?:Section\s+\d+|Act\s+No\.|Ordinance|Code|Principle|Rule)',
                    sentence,
                    re.IGNORECASE
                )
                
                if len(sentence.strip()) > 50:  # Only include substantial statements
                    statements.append({
                        "judge_name": judge_name or "Unknown",
                        "statement": sentence.strip(),
                        "legal_terms": legal_terms[:5]  # Limit to 5 terms
                    })
        
        return statements[:20]  # Limit to 20 most relevant statements
    
    def _extract_holdings(self, text: str, judge_names: List[str]) -> List[Dict]:
        """Extract key holdings (legal conclusions) from judgments"""
        holdings = []
        
        # Look for holding sections or conclusion paragraphs
        holding_patterns = [
            r'(?:HOLDING|CONCLUSION|DECISION|ORDER)[\s:]+(.+?)(?:\n\n|\Z)',
            r'(?:It\s+is\s+held|It\s+is\s+ordered|It\s+is\s+decided)[\s:]+(.+?)(?:\.|;|\n\n)',
            r'(?:Accordingly|Therefore|For\s+the\s+foregoing\s+reasons)[\s,]+(.+?)(?:\.|;|\n\n)',
        ]
        
        for pattern in holding_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                holding_text = match.group(1).strip()
                
                # Try to identify judge
                judge_name = None
                for name in judge_names:
                    if name.lower() in holding_text.lower():
                        judge_name = name
                        break
                
                if len(holding_text) > 30:  # Only substantial holdings
                    holdings.append({
                        "judge_name": judge_name or "Court",
                        "holding": holding_text[:500],  # Limit length
                        "type": "conclusion"
                    })
        
        return holdings[:10]  # Limit to 10 holdings
    
    def format_judge_info_for_context(self, judge_info: Dict) -> str:
        """Format judge information for use in LLM context"""
        if not judge_info.get("has_judge_info"):
            return ""
        
        formatted = "\n[JUDGE INFORMATION]:\n"
        
        if judge_info.get("judge_names"):
            formatted += f"Judges: {', '.join(judge_info['judge_names'])}\n"
        
        if judge_info.get("judge_holdings"):
            formatted += "\nKey Holdings:\n"
            for holding in judge_info["judge_holdings"][:3]:  # Top 3 holdings
                judge = holding.get("judge_name", "Court")
                text = holding.get("holding", "")[:200]
                formatted += f"- {judge}: {text}...\n"
        
        return formatted
