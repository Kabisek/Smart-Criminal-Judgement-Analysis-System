"""
Job Manager Service
Manages analysis jobs and their status
"""
from typing import Dict, Optional
from uuid import uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobManager:
    """Manages analysis jobs in memory"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
    
    def create_job(self, filename: str, file_path: str) -> str:
        """
        Create a new analysis job
        
        Args:
            filename: Original filename
            file_path: Path to uploaded file
            
        Returns:
            str: Job ID
        """
        job_id = str(uuid4())
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "uploaded",
            "filename": filename,
            "file_path": file_path,
            "progress": 0,
            "stage": "File uploaded",
            "created_at": datetime.now().isoformat(),
            "results": None,
            "error": None
        }
        logger.info(f"Created job {job_id} for file {filename}")
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        """
        Update job status and metadata
        
        Args:
            job_id: Job ID
            **kwargs: Fields to update
        """
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
            logger.debug(f"Updated job {job_id}: {kwargs}")
        else:
            logger.warning(f"Attempted to update non-existent job {job_id}")
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Get job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Dict: Job data or None
        """
        return self.jobs.get(job_id)
    
    def set_results(self, job_id: str, analyzed_case: Dict, arguments_report: Dict):
        """
        Store analysis results for a job
        
        Args:
            job_id: Job ID
            analyzed_case: Output File 1
            arguments_report: Output File 2
        """
        if job_id in self.jobs:
            self.jobs[job_id]["results"] = {
                "analyzed_case": analyzed_case,
                "arguments_report": arguments_report
            }
            self.jobs[job_id]["status"] = "completed"
            self.jobs[job_id]["progress"] = 100
            self.jobs[job_id]["stage"] = "Analysis completed"
            logger.info(f"Results stored for job {job_id}")
        else:
            logger.error(f"Attempted to store results for non-existent job {job_id}")

# Global job manager instance
job_manager = JobManager()
