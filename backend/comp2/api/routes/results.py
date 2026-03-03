"""
Results Route
Handles retrieving analysis results and downloads
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.models.schemas import ResultsResponse
from comp2.api.services.job_manager import job_manager

router = APIRouter()

@router.get("/results/{job_id}", response_model=ResultsResponse)
async def get_results(job_id: str):
    """
    Get the analysis results for a completed job
    
    Returns both Output File 1 (analyzed_case) and Output File 2 (arguments_report).
    """
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}"
        )
    
    if not job.get("results"):
        raise HTTPException(
            status_code=404,
            detail="Results not found for this job"
        )
    
    return {
        "job_id": job_id,
        "status": "completed",
        "analyzed_case": job["results"]["analyzed_case"],
        "arguments_report": job["results"]["arguments_report"]
    }

@router.get("/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """
    Download a specific result file as JSON
    
    file_type: "analysis" (Output File 1) or "arguments" (Output File 2)
    """
    if file_type not in ["analysis", "arguments"]:
        raise HTTPException(
            status_code=400,
            detail="file_type must be 'analysis' or 'arguments'"
        )
    
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Results not available. Job status: {job['status']}"
        )
    
    if not job.get("results"):
        raise HTTPException(
            status_code=404,
            detail="Results not found"
        )
    
    # Get the appropriate data
    if file_type == "analysis":
        data = job["results"]["analyzed_case"]
        filename = f"analyzed_case_{job_id}.json"
    else:
        data = job["results"]["arguments_report"]
        filename = f"arguments_report_{job_id}.json"
    
    return JSONResponse(
        content=data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
