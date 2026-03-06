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

# Model paths - updated to use improved models
MODEL_PATH = COMP3_DIR / "improved_ensemble_model.pkl"
SELECTOR_PATH = COMP3_DIR / "improved_selected_features.pkl"
LABEL_ENCODER_PATH = COMP3_DIR / "improved_label_encoder.pkl"
X_TRAIN_PATH = COMP3_DIR / "X_train_improved.csv"
BERT_EMBEDDINGS_PATH = COMP3_DIR / "bert_embeddings_train.npy"
DATASET_PATH = COMP3_DIR / "dataset_cleaned_v2.csv"
Y_TRAIN_PATH = COMP3_DIR / "y_train_improved.npy"
TFIDF_VECTORIZER_PATH = COMP3_DIR / "improved_tfidf_vectorizer.pkl"
SCALER_PATH = COMP3_DIR / "improved_scaler.pkl"

# BERT Model Configuration
BERT_MODEL_NAME = "nlpaueb/legal-bert-base-uncased"
BERT_MAX_LENGTH = 512

# Feature Configuration - updated for improved model
NUM_TRADITIONAL_FEATURES = 49
NUM_BERT_FEATURES = 100
NUM_TFIDF_FEATURES = 50
TOTAL_FEATURES = 199
SELECTED_FEATURES = 199

# Prediction thresholds
HIGH_CONFIDENCE_THRESHOLD = 60.0
MEDIUM_CONFIDENCE_THRESHOLD = 50.0

# Similar cases configuration
SIMILAR_CASES_TOP_K = 5
MIN_SIMILARITY_THRESHOLD = 30.0

# Class labels
CLASS_LABELS = ['Appeal_Allowed', 'Appeal_Dismissed', 'Partly_Allowed']

# Model metadata defaults - updated for improved model
DEFAULT_METADATA = {
    'accuracy': 0.7975,
    'model_name': 'Improved Calibrated Ensemble',
    'training_date': '2026-03-01',
    'training_samples': 1092,
    'num_features': 199
}
