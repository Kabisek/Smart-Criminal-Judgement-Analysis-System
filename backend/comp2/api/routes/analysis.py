"""
Analysis Route
Handles starting case analysis
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from comp2.api.models.schemas import AnalyzeRequest, AnalyzeResponse
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.services.job_manager import job_manager
import asyncio

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    Start analysis for an uploaded case file
    
    The analysis runs in the background. Use /status/{job_id} to check progress.
    """
    # Get job
    job = job_manager.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate job status
    if job["status"] != "uploaded":
        raise HTTPException(
            status_code=400,
            detail=f"Job status is '{job['status']}', expected 'uploaded'"
        )
    
    # Get options
    top_k = request.options.get("top_k", 10) if request.options else 10
    
    # Get analysis service
    try:
        analysis_service = get_analysis_service()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize analysis service: {str(e)}"
        )
    
    # Start processing in background
    job_manager.update_job(request.job_id, status="processing", progress=0)
    
    # Run analysis in background
    # FastAPI BackgroundTasks can handle async functions
    async def run_analysis_task():
        try:
            await analysis_service.process_case(request.job_id, job["file_path"], top_k)
        except Exception as e:
            # Error already logged and job status updated in process_case
            pass
    
    background_tasks.add_task(run_analysis_task)
    
    return {
        "job_id": request.job_id,
        "status": "processing",
        "message": "Analysis started successfully"
    }
