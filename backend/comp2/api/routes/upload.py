"""
Upload Route
Handles file uploads
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from comp2.api.services.job_manager import job_manager
from comp2.api.services.file_service import save_uploaded_file
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.models.schemas import AnalyzeCaseResponse
from comp2.api.config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE

router = APIRouter()

@router.post("/upload", response_model=AnalyzeCaseResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a case file for analysis
    
    Supported formats: PDF, TXT, JSON, DOCX
    Max file size: 10MB
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_ext} not allowed. Supported: {', '.join(ALLOWED_FILE_TYPES)}"
        )
    
    # Read file contents
    contents = await file.read()
    
    # Validate file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({len(contents)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )
    
    # Save file
    try:
        file_path = save_uploaded_file(file.filename, contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create job
    job_id = job_manager.create_job(file.filename, file_path)
    
    return {
        "job_id": job_id,
        "status": "uploaded",
        "filename": file.filename,
        "file_size": len(contents)
    }
