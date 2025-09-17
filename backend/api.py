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

@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables and Supabase connection"""
    import os
    from supabase_client import get_supabase_client, test_supabase_connection

    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "SUPABASE_URL": "SET" if os.getenv("SUPABASE_URL") else "NOT SET",
            "SUPABASE_KEY": "SET" if os.getenv("SUPABASE_KEY") else "NOT SET",
            "MISTRAL_API_KEY": "SET" if os.getenv("MISTRAL_API_KEY") else "NOT SET",
            "EMAIL_USER": "SET" if os.getenv("EMAIL_USER") else "NOT SET",
        },
        "supabase": {
            "client_available": get_supabase_client() is not None,
            "connection_test": test_supabase_connection()
        }
    }

    # Test loading a specific search
    try:
        from supabase_client import load_search_from_supabase
        test_search = load_search_from_supabase("eeb926d9-c50b-4071-97de-cbd30a13937f")
        debug_info["test_search"] = {
            "found": test_search is not None,
            "data": test_search if test_search else "Not found"
        }
    except Exception as e:
        debug_info["test_search"] = {
            "error": str(e)
        }

    return debug_info

@app.post("/api/test-email-integration")
async def test_email_integration():
    """Test the complete email integration with mock candidate data"""
    try:
        from mvp import send_email_with_results

        # Mock candidates for testing
        mock_candidates = [
            {
                'name': 'Test Kandidat 1',
                'location': 'Berlin, Deutschland',
                'url': 'https://resumes.indeed.com/resume/test1',
                'ai_response': 'Demo: Hervorragender Kandidat mit starken technischen Fähigkeiten und passender Erfahrung.'
            },
            {
                'name': 'Test Kandidat 2',
                'location': 'Hamburg, Deutschland',
                'url': 'https://resumes.indeed.com/resume/test2',
                'ai_response': 'Demo: Qualifizierte Frontend-Spezialistin mit modernen JavaScript-Frameworks.'
            }
        ]

        send_email_with_results(
            mock_candidates,
            "Test Keywords",
            "Berlin",
            25,
            "ndricim@beyondleverage.com",
            "API Email Integration Test"
        )

        return {
            "status": "success",
            "message": "Email integration test completed successfully",
            "candidates_sent": len(mock_candidates),
            "recipient": "ndricim@beyondleverage.com",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Email integration test failed: {str(e)}"
        )

@app.post("/api/test-email")
async def send_test_email():
    """Send a test email to verify email functionality and backend-frontend communication"""

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Get email configuration from environment variables (set in mvp.py)
        from mvp import EMAIL_USER, EMAIL_PASS, SMTP_SERVER, SMTP_PORT

        # Create test email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = "ndricim@beyondleverage.com"
        msg['Subject'] = "🧪 MatchTrex Backend Test - VPS Communication Check"

        # Test email body
        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                <h2 style="color: #2563eb; text-align: center;">🎉 Backend Test Successful!</h2>

                <p>Hallo Ndricim,</p>

                <p>Diese E-Mail bestätigt, dass die Kommunikation zwischen deinem Frontend und Backend erfolgreich funktioniert!</p>

                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #28a745;">✅ Test Details:</h3>
                    <ul>
                        <li><strong>Frontend:</strong> Erfolgreich deployed und erreichbar</li>
                        <li><strong>Backend:</strong> Läuft auf VPS Server (Port 8000)</li>
                        <li><strong>API Communication:</strong> ✅ Funktioniert</li>
                        <li><strong>Email Service:</strong> ✅ Funktioniert</li>
                        <li><strong>Environment Variables:</strong> ✅ Korrekt geladen</li>
                    </ul>
                </div>

                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #1976d2;">🔧 System Information:</h4>
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                    <p><strong>Server:</strong> VPS Backend</p>
                    <p><strong>Email Config:</strong> {email_user}</p>
                    <p><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</p>
                </div>

                <p style="margin-top: 30px;">
                    Du kannst jetzt mit dem vollständigen Deployment fortfahren! 🚀
                </p>

                <p style="color: #666; font-size: 14px; border-top: 1px solid #e0e0e0; padding-top: 15px; margin-top: 30px;">
                    Diese E-Mail wurde automatisch von der MatchTrex Backend API generiert.<br>
                    Test ausgeführt über Frontend → VPS Backend → Email Service
                </p>
            </div>
        </body>
        </html>
        """.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            email_user=EMAIL_USER,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT
        )

        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, "ndricim@beyondleverage.com", text)
        server.quit()

        return {
            "status": "success",
            "message": "Test email sent successfully to ndricim@beyondleverage.com",
            "timestamp": datetime.now().isoformat(),
            "email_config": {
                "from": EMAIL_USER,
                "to": "ndricim@beyondleverage.com",
                "smtp_server": f"{SMTP_SERVER}:{SMTP_PORT}"
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test email: {str(e)}"
        )

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

@app.post("/api/jobs/start-from-supabase")
async def start_job_from_supabase(request: dict, background_tasks: BackgroundTasks):
    """Start processing a search job from Supabase ID"""
    search_id = request.get('search_id')
    if not search_id:
        raise HTTPException(status_code=400, detail="search_id required")

    # Generate job ID for tracking
    job_id = str(uuid.uuid4())

    print(f"🎯 Starting backend job {job_id} for Supabase search {search_id}")

    # For now, we'll create a placeholder job entry
    job_status = JobStatus(
        job_id=job_id,
        status="pending",
        progress=f"Starting processing for search {search_id}...",
        created_at=datetime.now()
    )

    jobs[job_id] = job_status

    # Start background processing (Phase 2 will implement the actual processing)
    background_tasks.add_task(process_search_from_supabase_placeholder, job_id, search_id)

    return {"job_id": job_id, "status": "started", "message": f"Backend processing started for search {search_id}"}

# --- Background Job Processing ---

async def process_search_from_supabase_placeholder(job_id: str, search_id: str):
    """Process search job from Supabase with real integration"""
    try:
        print(f"📝 Processing job {job_id} for search {search_id}")

        # Import Supabase functions
        from supabase_client import (
            load_search_from_supabase,
            update_search_status,
            update_search_results,
            mark_search_failed
        )

        # 1. Load search from Supabase (with retry for race condition)
        search_data = None
        max_retries = 3
        for attempt in range(max_retries):
            search_data = load_search_from_supabase(search_id)
            if search_data:
                break
            print(f"   Attempt {attempt + 1}: Search not found, retrying in 2 seconds...")
            await asyncio.sleep(2)

        if not search_data:
            raise Exception(f"Search {search_id} not found in Supabase after {max_retries} attempts")

        print(f"✅ Loaded search data: {search_data.get('name', 'Unnamed')} - {search_data.get('search_keywords')}")

        # 2. Update job status (in memory)
        jobs[job_id].status = "running"
        jobs[job_id].progress = f"Processing search: {search_data.get('name', search_id)}"

        # 3. Update status in Supabase
        update_search_status(search_id, 'processing', 'Backend processing started...')

        # 4. Run REAL Pipeline!
        update_search_status(search_id, 'processing', 'Running Indeed search and AI processing...')

        # Import and run the real MVP pipeline
        from mvp import main_pipeline_for_api

        print(f"🚀 Starting REAL pipeline for search: {search_data.get('name', search_id)}")
        results = await asyncio.get_event_loop().run_in_executor(
            None, main_pipeline_for_api, search_data
        )

        print(f"✅ Pipeline completed! Found {results.get('filtered_count', 0)} qualified candidates")

        # 6. Update results in Supabase
        update_search_results(search_id, results)

        # 7. Update job status (in memory)
        jobs[job_id].status = "completed"
        jobs[job_id].progress = "Search completed successfully"
        jobs[job_id].results = results
        jobs[job_id].candidates_found = len(results["candidates"])
        jobs[job_id].completed_at = datetime.now()

        print(f"✅ Search {search_id} completed successfully with {len(results['candidates'])} candidates")

        # 8. TODO Phase 5: Send email notification

    except Exception as e:
        print(f"❌ Job {job_id} failed: {e}")

        # Update job status (in memory)
        jobs[job_id].status = "failed"
        jobs[job_id].error = str(e)
        jobs[job_id].progress = f"Error: {str(e)}"

        # Update status in Supabase
        mark_search_failed(search_id, str(e))

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
    import os

    parser = argparse.ArgumentParser(description="MatchTrex API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    # Use environment variable PORT if not specified via command line
    port = args.port or int(os.getenv("PORT", "8000"))
    host = args.host

    print(f"🚀 Starting MatchTrex API on http://{host}:{port}")

    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=args.reload
    )