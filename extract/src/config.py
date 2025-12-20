"""
Configuration Module
Handles environment variables and configuration
"""

import os
from dotenv import load_dotenv
from pathlib import Path


class Config:
    """Configuration class"""
    
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent / 'config' / '.env'
    load_dotenv(env_path)
    
    # API Configuration
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    
    # Primary API to use
    PRIMARY_API = os.getenv('PRIMARY_API', 'gemini').lower()
    
    # Output configuration
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', './output')
    
    # Application settings
    MAX_FILE_SIZE_MB = 50
    SUPPORTED_FORMATS = ['.pdf']

    MAX_EXTRACTION_CHARS = 30000
    MAX_EXTRACTION_TOKENS = 8000
    
    @classmethod
    def validate_api_config(cls) -> tuple[bool, str]:
        """
        Validate that required API configuration is present
        
        Returns:
            Tuple of (is_valid, message)
        """
        if cls.PRIMARY_API == 'deepseek':
            if not cls.DEEPSEEK_API_KEY:
                return False, "DEEPSEEK_API_KEY not configured in .env file"
        elif cls.PRIMARY_API == 'gemini':
            if not cls.GEMINI_API_KEY:
                return False, "GEMINI_API_KEY not configured in .env file"
        else:
            return False, f"Unknown PRIMARY_API: {cls.PRIMARY_API}. Use 'deepseek' or 'gemini'"
        
        return True, "Configuration is valid"
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get the API key for the primary API"""
        if cls.PRIMARY_API == 'deepseek':
            return cls.DEEPSEEK_API_KEY
        elif cls.PRIMARY_API == 'gemini':
            return cls.GEMINI_API_KEY
        return ''
