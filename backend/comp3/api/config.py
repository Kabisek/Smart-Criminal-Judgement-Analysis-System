"""
Configuration for Component 3: Appeal Outcome Decision Support
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent  # comp3/api/config.py → backend/
COMP3_DIR = Path(__file__).parent.parent  # comp3/api/config.py → comp3/
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
API_V1_PREFIX = "/api/v1/appeal"
ALLOWED_FILE_TYPES = [".pdf", ".txt", ".json", ".docx"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Model paths - now in comp3 directory
MODEL_PATH = COMP3_DIR / "appeal_outcome_imbalance_week7.pkl"
SELECTOR_PATH = COMP3_DIR / "selector_object.pkl"
LABEL_ENCODER_PATH = COMP3_DIR / "label_encoder_outcome.pkl"
X_TRAIN_PATH = COMP3_DIR / "X_train_bert.csv"
BERT_EMBEDDINGS_PATH = COMP3_DIR / "bert_embeddings_train.npy"
DATASET_PATH = COMP3_DIR / "dataset_cleaned_v2.csv"
Y_TRAIN_PATH = COMP3_DIR / "y_train_outcome.npy"

# BERT Model Configuration
BERT_MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
BERT_MAX_LENGTH = 512

# Feature Configuration
NUM_TRADITIONAL_FEATURES = 59
NUM_BERT_FEATURES = 768
TOTAL_FEATURES = 827
SELECTED_FEATURES = 150

# Prediction thresholds
HIGH_CONFIDENCE_THRESHOLD = 60.0
MEDIUM_CONFIDENCE_THRESHOLD = 50.0

# Similar cases configuration
SIMILAR_CASES_TOP_K = 5
MIN_SIMILARITY_THRESHOLD = 30.0

# Class labels
CLASS_LABELS = ['Appeal_Allowed', 'Appeal_Dismissed', 'Partly_Allowed']

# Model metadata defaults
DEFAULT_METADATA = {
    'accuracy': 0.6255,
    'model_name': 'XGBoost Custom Weights',
    'training_date': '2026-01-06',
    'training_samples': 1000,
    'num_features': 150
}
