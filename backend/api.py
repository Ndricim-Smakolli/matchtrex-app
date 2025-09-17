#!/usr/bin/env python3
"""
FastAPI wrapper for MatchTrex CV scraping pipeline
Provides REST API endpoints for the frontend to trigger searches
"""

import os
import sys
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the existing pipeline functions
from mvp import *  # Import all functions from existing mvp.py

# --- Request/Response Models ---

class SearchRequest(BaseModel):
    search_keywords: str
    location: Optional[str] = None
    resume_last_updated_days: Optional[int] = 30
    target_candidates: Optional[int] = 100
    max_radius: Optional[int] = 25
    recipient_email: Optional[str] = None
    user_prompt: Optional[str] = None
    system_prompt: Optional[str] = None

class SearchResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    candidates_found: Optional[int] = 0
    results: Optional[Dict] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

# --- Global Job Storage (In-Memory for MVP) ---
jobs: Dict[str, JobStatus] = {}

# --- FastAPI App Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 MatchTrex API starting up...")
    yield
    # Shutdown
    print("⭐ MatchTrex API shutting down...")

app = FastAPI(
    title="MatchTrex CV Scraping API",
    description="API for automated candidate sourcing and evaluation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/")
async def root():
    """API health check and information"""
    return {
        "service": "MatchTrex CV Scraping API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/jobs": "Create new search job",
            "GET /api/jobs/{job_id}": "Get job status",
            "GET /api/jobs": "List all jobs",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/jobs", response_model=SearchResponse)
async def create_search_job(request: SearchRequest, background_tasks: BackgroundTasks):
    """Create a new CV search job"""

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Create job entry
    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress="Initializing search...",
        created_at=datetime.now()
    )

    jobs[job_id] = job_status

    # Start background processing
    background_tasks.add_task(process_search_job, job_id, request)

    return SearchResponse(
        job_id=job_id,
        status="pending",
        message="Search job created successfully"
    )

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a specific job"""

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs (for debugging/admin)"""

    return {
        "jobs": list(jobs.values()),
        "total": len(jobs)
    }

# --- Background Job Processing ---

async def process_search_job(job_id: str, request: SearchRequest):
    """Process the CV search job in background"""

    try:
        # Update job status
        jobs[job_id].status = "running"
        jobs[job_id].progress = "Starting CV search pipeline..."

        # Convert request to dictionary for pipeline
        search_params = {
            "search_keywords": request.search_keywords,
            "location": request.location or "",
            "resume_last_updated_days": request.resume_last_updated_days or 30,
            "target_candidates": request.target_candidates or 100,
            "max_radius": request.max_radius or 25,
            "recipient_email": request.recipient_email or "",
            "user_prompt": request.user_prompt or "",
            "system_prompt": request.system_prompt or ""
        }

        # Update progress
        jobs[job_id].progress = "Searching Indeed for candidates..."

        # Run the actual pipeline (in a thread to avoid blocking)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, run_pipeline, search_params)

        # Update job with results
        jobs[job_id].status = "completed"
        jobs[job_id].progress = "Search completed successfully"
        jobs[job_id].results = results
        jobs[job_id].candidates_found = len(results.get('candidates', []))
        jobs[job_id].completed_at = datetime.now()

    except Exception as e:
        # Handle errors
        jobs[job_id].status = "failed"
        jobs[job_id].error = str(e)
        jobs[job_id].progress = f"Error: {str(e)}"
        print(f"Job {job_id} failed: {e}")

def run_pipeline(search_params: Dict) -> Dict:
    """
    Wrapper function to run the existing pipeline with new parameters
    This adapts the existing mvp.py functions to work with API requests
    """

    try:
        # TODO: Adapt the existing main() function from mvp.py
        # For now, return mock results

        # Simulate the existing pipeline steps:
        # 1. Search Indeed API
        # 2. Download CVs
        # 3. Filter with AI
        # 4. Send email results

        # This would call the actual pipeline functions
        results = {
            "candidates": [],
            "total_found": 0,
            "search_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }

        return results

    except Exception as e:
        raise Exception(f"Pipeline execution failed: {str(e)}")

# --- Development Server ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MatchTrex API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print(f"🚀 Starting MatchTrex API on http://{args.host}:{args.port}")

    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )