"""
Pydantic schemas for Appeal Outcome Prediction API
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PredictionProbabilities(BaseModel):
    """Prediction probabilities for each outcome"""
    Appeal_Allowed: float = Field(..., ge=0, le=100, description="Probability of Appeal Allowed (%)")
    Appeal_Dismissed: float = Field(..., ge=0, le=100, description="Probability of Appeal Dismissed (%)")
    Partly_Allowed: float = Field(..., ge=0, le=100, description="Probability of Partly Allowed (%)")

class DetectedFeatures(BaseModel):
    """Features detected from case description"""
    grounds: List[str] = Field(default_factory=list, description="Detected grounds of appeal")
    evidence: List[str] = Field(default_factory=list, description="Detected evidence types")
    offence: List[str] = Field(default_factory=list, description="Detected offence categories")
    other: List[str] = Field(default_factory=list, description="Other detected features")

class SimilarCase(BaseModel):
    """Similar historical case"""
    case_id: str = Field(..., description="Case identifier")
    similarity: float = Field(..., ge=0, le=100, description="Similarity percentage")
    outcome: str = Field(..., description="Case outcome")
    conviction_status: str = Field(..., description="Conviction status")
    facts: str = Field(..., description="Case facts summary")
    offence: str = Field(..., description="Offence type")
    high_court: str = Field(..., description="High court location")
    grounds: str = Field(..., description="Grounds of appeal")

class ModelMetadata(BaseModel):
    """Model metadata information"""
    accuracy: float = Field(..., ge=0, le=1, description="Model accuracy")
    model_name: str = Field(..., description="Model name/type")
    training_date: str = Field(..., description="Training date")
    training_samples: int = Field(..., ge=0, description="Number of training samples")
    num_features: int = Field(..., ge=0, description="Number of features")

class AppealPredictionRequest(BaseModel):
    """Request model for appeal prediction"""
    case_description: str = Field(..., min_length=50, description="Detailed case description")
    offence_type: Optional[str] = Field(None, description="Offence category")
    hc_sentence: Optional[str] = Field(None, description="High Court sentence")
    appeal_duration: Optional[int] = Field(None, ge=0, description="Appeal duration in days")
    
    class Config:
        schema_extra = {
            "example": {
                "case_description": "The accused was convicted by the High Court of Colombo for murder under Section 296...",
                "offence_type": "Murder",
                "hc_sentence": "Death penalty",
                "appeal_duration": 365
            }
        }

class AppealPredictionResponse(BaseModel):
    """Response model for appeal prediction"""
    status: str = Field(..., description="Prediction status")
    prediction: str = Field(..., description="Predicted outcome")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage")
    probabilities: PredictionProbabilities = Field(..., description="Detailed probabilities")
    detected_features: DetectedFeatures = Field(..., description="Detected features")
    similar_cases: List[SimilarCase] = Field(..., description="Similar historical cases")
    metadata: ModelMetadata = Field(..., description="Model metadata")
    timestamp: str = Field(..., description="Prediction timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "prediction": "Appeal_Allowed",
                "confidence": 67.8,
                "probabilities": {
                    "appeal_allowed": 67.8,
                    "appeal_dismissed": 25.1,
                    "partly_allowed": 7.1
                },
                "detected_features": {
                    "grounds": ["Contradictions", "Misdirection"],
                    "evidence": ["Eyewitness", "Medical"],
                    "offence": ["Murder"],
                    "other": []
                },
                "similar_cases": [
                    {
                        "case_id": "CA-123-2020",
                        "similarity": 85.2,
                        "outcome": "Appeal_Allowed",
                        "conviction_status": "Acquitted",
                        "facts": "Case involving...",
                        "offence": "Murder",
                        "high_court": "Colombo",
                        "grounds": "Procedural errors..."
                    }
                ],
                "metadata": {
                    "accuracy": 0.6255,
                    "model_name": "XGBoost Custom Weights",
                    "training_date": "2026-01-06",
                    "training_samples": 1000,
                    "num_features": 150
                },
                "timestamp": "2026-02-28T11:30:00"
            }
        }
