"""
PDF Processing Module
Handles PDF file upload and text extraction
"""

import pdfplumber
import os
from pathlib import Path
from typing import Tuple, Optional


class PDFProcessor:
    """Class to handle PDF file processing and text extraction"""
    
    def __init__(self, max_file_size_mb: int = 25):
        """
        Initialize PDF Processor
        
        Args:
            max_file_size_mb: Maximum allowed file size in MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.supported_formats = ['.pdf']
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if the uploaded file is a valid PDF
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(file_path):
            return False, "File not found"
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            return False, f"Unsupported file format. Only {self.supported_formats} allowed"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"File size exceeds {self.max_file_size_mb}MB limit"
        
        return True, "File is valid"
    
    def extract_text(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (success, message, extracted_text)
        """
        try:
            # Validate file first
            is_valid, validation_msg = self.validate_file(file_path)
            if not is_valid:
                return False, validation_msg, None
            
            # Extract text from PDF
            extracted_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text()
                    extracted_text += "\n---PAGE BREAK---\n"
            
            if not extracted_text.strip():
                return False, "No text found in PDF", None
            
            return True, "Text extracted successfully", extracted_text
        
        except Exception as e:
            return False, f"Error extracting text: {str(e)}", None
    
    def extract_metadata(self, file_path: str) -> dict:
        """
        Extract metadata from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            metadata = {}
            with pdfplumber.open(file_path) as pdf:
                metadata['total_pages'] = len(pdf.pages)
                metadata['pdf_info'] = pdf.metadata
            
            metadata['file_name'] = Path(file_path).name
            metadata['file_size_mb'] = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            
            return metadata
        except Exception as e:
            return {'error': str(e)}
