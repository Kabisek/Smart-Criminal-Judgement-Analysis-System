"""
Configuration for Component 2 - Adversarial Case Analysis
ChromaDB-only retrieval (no feature_vectors.pkl, no merged_v2.csv at runtime)
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent  # comp2/api/config.py → backend/
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
MODELS_DIR = DATA_DIR / "models"  # Trained models (K-Means, etc.) copied from backend2

# Create necessary directories
UPLOADS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# API Configuration
API_V1_PREFIX = "/api/v1"
ALLOWED_FILE_TYPES = [".pdf", ".txt", ".json", ".docx"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

# ChromaDB Vector Store - Component 2 only (separate from Component 1's chroma_db)
# Comp1 uses: data/chroma_db (collection: legal_knowledge_base)
# Comp2 uses: data/chroma_db_comp2 (collection: legal_cases)
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db_comp2"
CHROMA_COLLECTION_NAME = "legal_cases"

# Embedding Model Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "nlpaueb/legal-bert-base-uncased")
FINE_TUNED_MODEL_PATH = os.getenv("FINE_TUNED_MODEL_PATH", None)
