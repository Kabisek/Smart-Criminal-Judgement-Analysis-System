"""
Component 3: Appeal Outcome Decision Support
Handles: appeal outcome prediction, case similarity analysis, feature detection
"""

from .api.config import API_V1_PREFIX
from .src.core.models import AppealPredictor
from .api.services.prediction_service import PredictionService

__all__ = ['API_V1_PREFIX', 'AppealPredictor', 'PredictionService']
