"""
Helper utility functions
"""
from datetime import datetime
from typing import Dict

def estimate_time_remaining(job: Dict) -> int:
    """
    Estimate remaining time in seconds based on progress
    
    Args:
        job: Job dictionary with progress and created_at
        
    Returns:
        int: Estimated seconds remaining
    """
    progress = job.get("progress", 0)
    if progress == 0:
        return 120  # 2 minutes default
    elif progress >= 100:
        return 0
    
    # Simple linear estimation
    created_at = job.get("created_at")
    if not created_at:
        return 60
    
    try:
        if isinstance(created_at, str):
            created_time = datetime.fromisoformat(created_at)
        else:
            created_time = created_at
        
        elapsed = (datetime.now() - created_time).total_seconds()
        if progress > 0 and elapsed > 0:
            total_estimated = (elapsed / progress) * 100
            remaining = total_estimated - elapsed
            return max(0, int(remaining))
    except Exception:
        pass
    
    return 60
