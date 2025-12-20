"""
AI Information Extraction Module
Handles extraction using Deepseek or Gemini APIs
"""

import os
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import json
import time


class AIExtractor(ABC):
    """Abstract base class for AI extractors"""
    
    @abstractmethod
    def extract_judgment_info(self, text: str) -> Dict:
        """Extract judgment information from text"""
        pass
    
    def get_extraction_prompt(self) -> str:
        """Get the prompt for extracting judgment information"""
        return """
        Please extract the following information from the criminal judgment document.
        Return the output strictly as a JSON object containing these exact keys only.

        If any information is missing:
        - Use "Not Found" for text fields
        - Use "No" for Yes/No fields
        - Use 0 for numeric fields


        ------------------------------------------------------------
        CASE IDENTIFICATION
        ------------------------------------------------------------
        1. source_file_name
        2. court_of_appeal_case_no
        3. high_court_case_no
        4. high_court_location


        ------------------------------------------------------------
        DATES
        ------------------------------------------------------------
        5. judgment_date_coa
        6. judgment_date_hc
        7. date_of_offence


        ------------------------------------------------------------
        PARTIES
        ------------------------------------------------------------
        8. judges


        ------------------------------------------------------------
        OFFENCE DETAILS
        ------------------------------------------------------------
        9. offence_sections
        10. offence_category
        11. location_of_offence


        ------------------------------------------------------------
        CASE TYPE
        ------------------------------------------------------------
        12. language_of_criminal


        ------------------------------------------------------------
        FACTS & EVIDENCE
        ------------------------------------------------------------
        13. brief_facts_summary
        14. evidence_type_primary
        15. evidence_type_secondary


        ------------------------------------------------------------
        HIGH COURT DECISION
        ------------------------------------------------------------
        17. hc_offence_of_conviction_sections
        18. hc_sentence_type(Death/Life/Rigorous Imprisonment/ etc.)
        19. hc_fine_amount
        20. hc_compensation_amount
        21. hc_judgment_summary


        ------------------------------------------------------------
        GROUNDS OF APPEAL
        ------------------------------------------------------------
        22. grounds_of_appeal_raw_text_summary
        23. grounds_of_appeal_structured_notes
        24. gnd_contradictions (Yes/No)
        25. gnd_chain_of_custody (Yes/No)
        26. gnd_illegal_search_or_raid (Yes/No)
        27. gnd_wrong_identification (Yes/No)
        28. gnd_dying_declaration_validity (Yes/No)
        29. gnd_circumstantial_insufficient (Yes/No)
        30. gnd_medical_inconsistency (Yes/No)
        31. gnd_misdirection_on_law (Yes/No)
        32. gnd_procedural_error (Yes/No)
        33. gnd_new_evidence (Yes/No)
        34. gnd_sentence_excessive_or_inadequate (Yes/No)
        35. gnd_delay_prejudice (Yes/No)
        36. gnd_judicial_bias_or_unfair_trial (Yes/No)
        37. gnd_other (Yes/No)
        38. gnd_other_description


        ------------------------------------------------------------
        WITNESS & EVIDENCE ANALYSIS
        ------------------------------------------------------------
        39. witness_evidence_analysis_summary
        40. num_prosecution_witnesses
        41. num_defence_witnesses
        42. eyewitness_present (Yes/No)
        43. child_witness_present (Yes/No)
        44. expert_evidence_present (Yes/No)
        45. medical_evidence_strength (Strong/Moderate/Weak/None)
        46. forensic_evidence_present (Yes/No)
        47. chain_of_custody_quality (good/moderate/weak/none)
        48. dying_declaration_present (yes/no)
        49. dying_declaration_reliability (Reliable/Doubtful/Unreliable)
        50. confession_present (Yes/No)
        51. circumstantial_case (Yes/No)
        52. probability_assessment_by_court


        ------------------------------------------------------------
        DEFENCE
        ------------------------------------------------------------
        53. defence_version_summary ( Include: defence_alibi_claimed , dock_statement_only
                                        defence_called_witnesses , defence_credibility_assessment


        ------------------------------------------------------------
        LEGAL ANALYSIS
        ------------------------------------------------------------
        54. legal_errors_identified (Yes/No)
        55. legal_errors_description
        56. procedural_defects_present (Yes/No)
        57. procedural_defects_description
        58. directions_on_burden_of_proof_correct (Yes/No)


        ------------------------------------------------------------
        COURT OF APPEAL ANALYSIS
        ------------------------------------------------------------
        59. court_of_appeal_analysis_summary
        (Include: coa_key_reasons_for_outcome, coa_view_on_prosecution_credibility,
        coa_view_on_defence_credibility, coa_on_contradictions,
        coa_on_chain_of_custody, coa_on_circumstantial_evidence,
        coa_on_dying_declaration, coa_on_sentence, coa_applied_precedents)


        ------------------------------------------------------------
        FINAL OUTCOME
        ------------------------------------------------------------
        60. coa_final_outcome_class (Appeal Allowed/Dismissed/Partly Allowed/ etc.)
        61. coa_conviction_status (Convicted/Acquitted/Modified)
        62. coa_sentence_type
        63. coa_fine_amount
        64. coa_compensation_amount


        ------------------------------------------------------------
        TEXT
        ------------------------------------------------------------
        65. full_text_judgment

        """


class DeepseekExtractor(AIExtractor):
    """Deepseek API based extractor"""
    
    def __init__(self, api_key: str):
        """
        Initialize Deepseek Extractor
        
        Args:
            api_key: Deepseek API key
        """
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
    
    def extract_judgment_info(self, text: str) -> Dict:
        """
        Extract judgment information using Deepseek API
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Dictionary containing extracted information
        """
        try:
            import requests
            
            # Truncate text if too long (Deepseek has token limits)
            max_chars = 30000
            truncated_text = text[:max_chars]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert legal document analyzer specializing in criminal judgments."
                    },
                    {
                        "role": "user",
                        "content": f"{self.get_extraction_prompt()}\n\nDocument:\n{truncated_text}"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 8000
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON from response
                try:
                    extracted_data = json.loads(content)
                    return extracted_data
                except json.JSONDecodeError:
                    return self._parse_text_response(content)
            else:
                return {"error": f"API Error: {response.status_code}", "message": response.text}
        
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_text_response(self, response: str) -> Dict:
        """Parse text response if JSON parsing fails"""
        # Try to extract JSON from the response text
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return {"raw_response": response}


class GeminiExtractor(AIExtractor):
    """Google Gemini API based extractor"""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini Extractor
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-pro')
        except ImportError:
            raise ImportError("google-generativeai package not installed")
    
    def extract_judgment_info(self, text: str) -> Dict:
        """
        Extract judgment information using Gemini API
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            Dictionary containing extracted information
        """
        try:
            import google.generativeai as genai
            
            # Truncate text if too long (Gemini has token limits)
            max_chars = 30000
            truncated_text = text[:max_chars]
            
            prompt = f"{self.get_extraction_prompt()}\n\nDocument:\n{truncated_text}"
            
            response = self.client.generate_content(prompt)
            content = response.text
            
            # Parse JSON from response
            try:
                extracted_data = json.loads(content)
                return extracted_data
            except json.JSONDecodeError:
                return self._parse_text_response(content)
        
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_text_response(self, response: str) -> Dict:
        """Parse text response if JSON parsing fails"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return {"raw_response": response}


class ExtractorFactory:
    """Factory class to create appropriate extractor"""
    
    @staticmethod
    def create_extractor(api_type: str, api_key: str) -> Optional[AIExtractor]:
        """
        Create an extractor based on API type
        
        Args:
            api_type: Type of API ('deepseek' or 'gemini')
            api_key: API key for the service
            
        Returns:
            Appropriate extractor instance or None
        """
        if api_type.lower() == 'deepseek':
            return DeepseekExtractor(api_key)
        elif api_type.lower() == 'gemini':
            return GeminiExtractor(api_key)
        else:
            raise ValueError(f"Unknown API type: {api_type}")
