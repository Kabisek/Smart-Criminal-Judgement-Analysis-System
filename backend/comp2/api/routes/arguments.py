"""
Arguments Route
Handles argument points generation (Output File 2)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from comp2.api.services.file_service import save_uploaded_file
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE
from comp2.api.models.schemas import ArgumentsResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/arguments", response_model=ArgumentsResponse)
async def generate_arguments(file: UploadFile = File(...)):
    """
    Generate argument points and strategic arguments report
    
    This endpoint:
    1. Validates and saves the uploaded file
    2. Extracts text from the file
    3. Cleans and preprocesses the text
    4. Generates embeddings using Legal-BERT
    5. Finds similar cases
    6. Generates strategic arguments report (Output File 2)
    
    Args:
        file: Case file (PDF, TXT, JSON, DOCX)
    
    Returns:
        ArgumentsResponse with arguments report data
    """
    try:
        # Step 1: Validate file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Step 2: Read and validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(contents)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
            )
        
        logger.info(f"Generating arguments for file: {file.filename} ({len(contents)} bytes)")
        
        # Step 3: Save file
        try:
            file_path = save_uploaded_file(file.filename, contents)
            logger.info(f"File saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Step 4: Get analysis service
        try:
            analysis_service = get_analysis_service()
        except Exception as e:
            logger.error(f"Failed to initialize analysis service: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize analysis service: {str(e)}"
            )
        
        # Step 5: Generate arguments report
        logger.info(f"Starting arguments generation for {file.filename}...")
        try:
            arguments_report = await analysis_service.generate_arguments(file_path=file_path)
            logger.info(f"Arguments generation completed for {file.filename}")
        except Exception as e:
            logger.error(f"Error during arguments generation: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Arguments generation failed: {str(e)}"
            )
        
        # Step 6: Extract similar cases count
        similar_cases_count = len(arguments_report.get("similar_cases", []))
        
        # Step 7: Return results
        return {
            "filename": file.filename,
            "file_size": len(contents),
            "arguments_report": arguments_report,
            "similar_cases_count": similar_cases_count,
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_arguments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
