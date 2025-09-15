"""
Job Queue Models for MatchTrex Async Pipeline
Pydantic models for job creation, status tracking, and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    """Job type enumeration"""
    CANDIDATE_SEARCH = "candidate_search"

class JobCreateRequest(BaseModel):
    """Request model for creating a new job"""
    job_type: JobType = JobType.CANDIDATE_SEARCH
    search_keywords: str = Field(..., description="Keywords for job search")
    location: Optional[str] = Field(None, description="Location for search")
    resume_last_updated_days: Optional[int] = Field(30, description="Resume age filter in days")
    target_candidates: Optional[int] = Field(100, description="Target number of candidates")
    max_radius: Optional[int] = Field(25, description="Search radius in km")
    recipient_email: str = Field(..., description="Email for results")
    user_prompt: Optional[str] = Field(None, description="Custom AI prompt")
    system_prompt: Optional[str] = Field(None, description="System AI prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "search_keywords": "python developer",
                "location": "Berlin",
                "resume_last_updated_days": 30,
                "target_candidates": 50,
                "max_radius": 25,
                "recipient_email": "user@example.com",
                "user_prompt": "Find experienced Python developers",
                "system_prompt": "Focus on backend development skills"
            }
        }

class JobProgress(BaseModel):
    """Progress information for a job"""
    step: str = Field(..., description="Current processing step")
    progress_percent: float = Field(0.0, ge=0, le=100, description="Progress percentage")
    candidates_found: int = Field(0, description="Number of candidates found so far")
    current_action: str = Field("", description="Current action being performed")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

class JobResult(BaseModel):
    """Job result data"""
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    total_found: int = 0
    qualified_count: int = 0
    summary: Dict[str, Any] = Field(default_factory=dict)
    email_sent: bool = False

class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = JobStatus.PENDING
    message: str = "Job created successfully"
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Job created successfully",
                "created_at": "2025-09-15T10:30:00Z"
            }
        }

class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    job_id: str
    status: JobStatus
    progress: Optional[JobProgress] = None
    result: Optional[JobResult] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123e4567-e89b-12d3-a456-426614174000",
                "status": "running",
                "progress": {
                    "step": "scraping_indeed",
                    "progress_percent": 45.0,
                    "candidates_found": 23,
                    "current_action": "Downloading CV files...",
                    "estimated_completion": "2025-09-15T11:15:00Z"
                },
                "created_at": "2025-09-15T10:30:00Z",
                "started_at": "2025-09-15T10:31:00Z"
            }
        }

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    job_id: str
    message_type: str = Field(..., description="Type of message (status_update, progress, error, completed)")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123e4567-e89b-12d3-a456-426614174000",
                "message_type": "progress",
                "data": {
                    "status": "running",
                    "progress_percent": 65.0,
                    "candidates_found": 34,
                    "current_action": "Processing CVs with AI..."
                },
                "timestamp": "2025-09-15T10:45:00Z"
            }
        }

def generate_job_id() -> str:
    """Generate a unique job ID"""
    return f"job_{uuid.uuid4()}"

# Job storage (in-memory for MVP, will be moved to database later)
job_storage: Dict[str, Dict[str, Any]] = {}

def create_job_entry(job_id: str, request: JobCreateRequest) -> Dict[str, Any]:
    """Create a new job entry in storage"""
    job_entry = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "job_type": request.job_type,
        "parameters": request.dict(),
        "progress": None,
        "result": None,
        "error_message": None,
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "websocket_connections": set()
    }

    # Also persist to Supabase if available
    try:
        from supabase_service import supabase_service

        if supabase_service.is_available():
            supabase_service.save_job(job_entry)
    except Exception as e:
        # Don't fail if Supabase fails - just log
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Failed to persist job to Supabase: {e}")

    return job_entry

def update_job_status(job_id: str, status: JobStatus, **kwargs) -> bool:
    """Update job status and optional fields"""
    if job_id not in job_storage:
        return False

    job_storage[job_id]["status"] = status

    # Update optional fields
    for key, value in kwargs.items():
        if key in ["progress", "result", "error_message", "started_at", "completed_at"]:
            job_storage[job_id][key] = value

    # Also persist to Supabase if available
    try:
        from supabase_service import supabase_service

        if supabase_service.is_available():
            supabase_service.update_job_status(
                job_id=job_id,
                status=status.value if hasattr(status, 'value') else str(status),
                progress=kwargs.get("progress").dict() if kwargs.get("progress") and hasattr(kwargs.get("progress"), 'dict') else kwargs.get("progress"),
                result=kwargs.get("result").dict() if kwargs.get("result") and hasattr(kwargs.get("result"), 'dict') else kwargs.get("result"),
                error_message=kwargs.get("error_message"),
                completed_at=kwargs.get("completed_at")
            )
    except Exception as e:
        # Don't fail if Supabase fails - just log
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Failed to persist job status to Supabase: {e}")

    return True

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    return job_storage.get(job_id)

def get_all_jobs() -> Dict[str, Dict[str, Any]]:
    """Get all jobs (for debugging/admin)"""
    return job_storage.copy()