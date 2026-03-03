"""
Health check routes for Component 3
"""
from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint for Component 3
    
    Returns:
        Health status information
    """
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Appeal Outcome Decision Support",
            "component": "comp3",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
