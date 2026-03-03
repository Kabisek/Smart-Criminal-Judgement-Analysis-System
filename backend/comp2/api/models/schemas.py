"""
Pydantic models for API request/response schemas
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class UploadResponse(BaseModel):
    """Response model for file upload"""
    job_id: str
    status: str
    filename: str
    file_size: int

class AnalyzeRequest(BaseModel):
    """Request model for starting analysis"""
    job_id: str
    options: Optional[Dict[str, Any]] = {"top_k": 10}

class AnalyzeResponse(BaseModel):
    """Response model for analysis start"""
    job_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: int
    stage: str
    estimated_time_remaining: int

class ResultsResponse(BaseModel):
    """Response model for analysis results"""
    job_id: str
    status: str
    analyzed_case: Dict[str, Any]
    arguments_report: Dict[str, Any]

class ProcessResponse(BaseModel):
    """Response model for unified process endpoint"""
    filename: str
    file_size: int
    analyzed_case: Dict[str, Any]
    arguments_report: Dict[str, Any]
    similar_cases_count: int
    status: str

class AnalyzeCaseResponse(BaseModel):
    """Response model for case analysis endpoint"""
    filename: str
    file_size: int
    analyzed_case: Dict[str, Any]
    status: str


class SourceSpan(BaseModel):
    """A mapping from an extracted field back to its location in the source text."""
    field_id: str
    page: int
    start_char: int
    end_char: int
    matched_text: str


class PageText(BaseModel):
    page_num: int
    text: str


class AnalyzeCaseWithSpansResponse(BaseModel):
    """Extended response that includes bounding-box data for the document viewer."""
    filename: str
    file_size: int
    analyzed_case: Dict[str, Any]
    document_text: List[PageText] = []
    source_spans: List[SourceSpan] = []
    status: str


class ArgumentsResponse(BaseModel):
    """Response model for arguments generation endpoint"""
    filename: str
    file_size: int
    arguments_report: Dict[str, Any]
    similar_cases_count: int
    status: str
