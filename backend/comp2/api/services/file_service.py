"""
File Service
Handles file uploads and storage
"""
import os
from pathlib import Path
from datetime import datetime
from comp2.api.config import UPLOADS_DIR

def save_uploaded_file(filename: str, contents: bytes) -> str:
    """
    Save uploaded file to disk
    
    Args:
        filename: Original filename
        contents: File contents as bytes
        
    Returns:
        str: Path to saved file
    """
    # Create unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    return str(file_path)
