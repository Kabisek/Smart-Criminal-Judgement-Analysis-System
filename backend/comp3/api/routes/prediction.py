"""
Prediction routes for Appeal Outcome Decision Support
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from comp3.api.models.schemas import AppealPredictionRequest, AppealPredictionResponse
from comp3.api.services.prediction_service import get_prediction_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/predict", response_model=AppealPredictionResponse)
async def predict_appeal_outcome(request: AppealPredictionRequest):
    """
    Predict appeal outcome for a given case
    
    This endpoint:
    1. Validates the case description
    2. Extracts features using NLP and BERT
    3. Runs the ensemble prediction model
    4. Finds similar historical cases
    5. Returns comprehensive prediction results
    
    Args:
        request: Appeal prediction request with case details
        
    Returns:
        AppealPredictionResponse with prediction results
        
    Raises:
        HTTPException: If prediction fails
    """
    try:
        # Validate input
        if len(request.case_description.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Case description must be at least 50 characters long"
            )
        
        logger.info(f"Received prediction request for case description length: {len(request.case_description)}")
        
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make prediction
        result = await prediction_service.predict_appeal_outcome(request.case_description)
        
        # Convert to response model
        response = AppealPredictionResponse(**result)
        
        logger.info(f"Prediction completed: {response.prediction} with {response.confidence:.1f}% confidence")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in predict_appeal_outcome: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )

@router.get("/model/info")
async def get_model_info():
    """
    Get model information and status
    
    Returns:
        Dictionary with model metadata and status
    """
    try:
        prediction_service = get_prediction_service()
        model_info = await prediction_service.get_model_info()
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )
