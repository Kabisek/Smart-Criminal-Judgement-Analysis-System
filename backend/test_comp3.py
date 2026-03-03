#!/usr/bin/env python3
"""
Test script to identify Component 3 initialization issues
"""

import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("Testing Component 3 initialization...")
    
    # Test imports
    from comp3.api.services.prediction_service import get_prediction_service
    
    # Test service initialization
    print("Creating prediction service...")
    prediction_service = get_prediction_service()
    
    # Test prediction with simple case
    print("Testing prediction...")
    test_case = "Test case description with enough characters to pass validation and test the prediction system functionality."
    
    import asyncio
    result = asyncio.run(prediction_service.predict_appeal_outcome(test_case))
    
    print("✅ Component 3 test successful!")
    print(f"Result: {result}")
    
except Exception as e:
    print(f"❌ Component 3 test failed: {e}")
    import traceback
    traceback.print_exc()
