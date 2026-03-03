"""
Configuration for the FastAPI backend
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent  # comp2/api/config.py → comp2/api/ → comp2/ → backend/
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
FEATURES_DIR = DATA_DIR / "features"
PROCESSED_DIR = DATA_DIR / "processed"
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

# Create necessary directories
UPLOADS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# API Configuration
API_V1_PREFIX = "/api/v1"
ALLOWED_FILE_TYPES = [".pdf", ".txt", ".json", ".docx"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React dev server
    "http://127.0.0.1:5173",
]

# Model paths
FEATURE_VECTORS_PATH = FEATURES_DIR / "feature_vectors.pkl"
NEAREST_NEIGHBORS_MODEL_PATH = MODELS_DIR / "final_nearest_neighbors_model.pkl"
CLEANED_CASES_CSV_PATH = PROCESSED_DIR / "cleaned_cases.csv"

# Embedding Model Configuration
# Option 1: Use pre-trained Legal-BERT (recommended for legal domain)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "nlpaueb/legal-bert-base-uncased")

# Option 2: Use fine-tuned Legal-BERT model (if you have one)
# Set this to the path of your fine-tuned model directory
# Example: "data/models/sri_lanka_legal_bert" or "/path/to/your/fine-tuned-model"
FINE_TUNED_MODEL_PATH = os.getenv("FINE_TUNED_MODEL_PATH", None)

# If FINE_TUNED_MODEL_PATH is set, it will be used instead of EMBEDDING_MODEL_NAME
# Otherwise, EMBEDDING_MODEL_NAME will be used (defaults to Legal-BERT)
