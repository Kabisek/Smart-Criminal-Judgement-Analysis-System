"""
Status Route
Handles job status queries
"""
from fastapi import APIRouter, HTTPException
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.models.schemas import StatusResponse
from comp2.api.services.job_manager import job_manager
from comp2.api.utils.helpers import estimate_time_remaining

router = APIRouter()

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get the current status of an analysis job
    
    Returns progress, current stage, and estimated time remaining.
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate estimated time remaining
    estimated_time = estimate_time_remaining(job)
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "stage": job.get("stage", ""),
        "estimated_time_remaining": estimated_time
    }
