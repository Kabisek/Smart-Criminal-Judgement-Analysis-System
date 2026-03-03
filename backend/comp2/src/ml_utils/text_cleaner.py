"""
Text Cleaning and Preprocessing Module
Cleans and normalizes legal text for ML processing
"""

import re
import string
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    """Clean and preprocess legal text documents"""
    
    def __init__(self):
        self.min_text_length = 100  # Minimum characters for valid text
        
    def clean_text(self, text: str, remove_extra_spaces: bool = True) -> str:
        """
        Clean a single text document
        
        Args:
            text: Raw text to clean
            remove_extra_spaces: Whether to remove extra whitespace
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and other control characters
        text = text.replace('\x00', ' ')
        text = re.sub(r'[\x01-\x08\x0b-\x0c\x0e-\x1f]', ' ', text)
        
        # Normalize whitespace
        if remove_extra_spaces:
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Preserve paragraph breaks
        
        # Remove excessive punctuation (keep single instances)
        text = re.sub(r'[.]{3,}', '...', text)  # Multiple dots → ellipsis
        text = re.sub(r'[-]{3,}', '---', text)  # Multiple dashes
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_sections(self, text: str) -> dict:
        """
        Extract key sections from legal document (if structured)
        
        Args:
            text: Legal document text
            
        Returns:
            dict: Extracted sections (facts, judgment, etc.)
        """
        sections = {
            "full_text": text,
            "has_structure": False
        }
        
        # Try to identify common legal document sections
        # This is a basic implementation - can be enhanced
        
        # Look for common section headers
        section_patterns = {
            "facts": r"(?:facts?|background|case facts?|incident)[\s:]*",
            "judgment": r"(?:judgment|decision|order|ruling)[\s:]*",
            "evidence": r"(?:evidence|exhibits?|documents?)[\s:]*",
            "statutes": r"(?:statutes?|sections?|acts?|ordinances?)[\s:]*"
        }
        
        text_lower = text.lower()
        for section_name, pattern in section_patterns.items():
            if re.search(pattern, text_lower):
                sections[section_name] = True
                sections["has_structure"] = True
            else:
                sections[section_name] = False
        
        return sections
    
    def is_valid_text(self, text: str) -> bool:
        """
        Check if text is valid for processing
        
        Args:
            text: Text to validate
            
        Returns:
            bool: True if text is valid
        """
        if not isinstance(text, str):
            return False
        
        # Check minimum length
        if len(text.strip()) < self.min_text_length:
            return False
        
        # Check if text has meaningful content (not just special characters)
        alpha_count = sum(1 for c in text if c.isalpha())
        if alpha_count < 50:  # At least 50 alphabetic characters
            return False
        
        return True
    
    def preprocess_dataframe(self, df: pd.DataFrame, text_column: str = "full_text") -> pd.DataFrame:
        """
        Preprocess a DataFrame of documents
        
        Args:
            df: DataFrame with text documents
            text_column: Name of column containing text
            
        Returns:
            pd.DataFrame: DataFrame with cleaned texts and validation flags
        """
        df = df.copy()
        
        print(f"Cleaning {len(df)} documents...")
        
        # Clean texts
        df['cleaned_text'] = df[text_column].apply(self.clean_text)
        
        # Validate texts
        df['is_valid'] = df['cleaned_text'].apply(self.is_valid_text)
        
        # Calculate text statistics
        df['text_length'] = df['cleaned_text'].apply(len)
        df['word_count'] = df['cleaned_text'].apply(lambda x: len(x.split()) if isinstance(x, str) else 0)
        
        # Extract sections (basic) - optional, can be skipped for faster processing
        try:
            print("Extracting document sections...")
            sections_list = df['cleaned_text'].apply(self.extract_sections)
            
            # Add section flags to DataFrame
            for section_name in ["has_structure", "facts", "judgment", "evidence", "statutes"]:
                df[f"has_{section_name}"] = sections_list.apply(lambda x: x.get(section_name, False) if isinstance(x, dict) else False)
        except Exception as e:
            logger.warning(f"Section extraction skipped: {e}")
            # Add empty section flags if extraction fails
            for section_name in ["has_structure", "facts", "judgment", "evidence", "statutes"]:
                df[f"has_{section_name}"] = False
        
        # Filter out invalid texts
        valid_count = df['is_valid'].sum()
        print(f"\n Preprocessing complete!")
        print(f"   Valid documents: {valid_count}/{len(df)}")
        print(f"   Removed invalid: {len(df) - valid_count}")
        
        return df
    
    def filter_valid_documents(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter DataFrame to keep only valid documents
        
        Args:
            df: DataFrame with documents
            
        Returns:
            pd.DataFrame: Filtered DataFrame with only valid documents
        """
        return df[df['is_valid'] == True].copy()

