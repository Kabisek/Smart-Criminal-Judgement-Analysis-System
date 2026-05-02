"""
Case Analysis Route
Handles case analysis generation (Output File 1)
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
from comp2.api.services.file_service import save_uploaded_file
from comp2.api.services.analysis_service import get_analysis_service
from comp2.api.config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE
from comp2.api.models.schemas import AnalyzeCaseResponse, AnalyzeCaseWithSpansResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeCaseWithSpansResponse)
async def analyze_case(file: UploadFile = File(...)):
    """
    Analyze a case file and generate comprehensive case analysis.

    Returns the analyzed case together with document_text (raw page texts)
    and source_spans (character-offset mappings for bounding-box highlighting).
    """
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported: {', '.join(ALLOWED_FILE_TYPES)}"
            )

        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(contents)} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
            )

        logger.info(f"Analyzing case file: {file.filename} ({len(contents)} bytes)")

        try:
            file_path = save_uploaded_file(file.filename, contents)
            logger.info(f"File saved to: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        try:
            analysis_service = get_analysis_service()
        except Exception as e:
            logger.error(f"Failed to initialize analysis service: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize analysis service: {str(e)}")

        logger.info(f"Starting case analysis for {file.filename}...")
        try:
            result = await analysis_service.analyze_case(file_path=file_path)
            logger.info(f"Case analysis completed for {file.filename}")
        except Exception as e:
            logger.error(f"Error during case analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Case analysis failed: {str(e)}")

        analyzed_case = {k: v for k, v in result.items() if k not in ("document_text", "source_spans")}

        return {
            "filename": file.filename,
            "file_size": len(contents),
            "analyzed_case": analyzed_case,
            "document_text": result.get("document_text", []),
            "source_spans": result.get("source_spans", []),
            "status": "completed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_case: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
