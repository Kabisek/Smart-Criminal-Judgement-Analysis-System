"""
API routes for Component 3
"""

from .prediction import router as prediction_router
from .health import router as health_router

__all__ = ['prediction_router', 'health_router']
