"""
Background Job Worker System for MatchTrex
Handles async job processing using ThreadPoolExecutor
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
import logging

from job_models import (
    JobStatus, JobProgress, JobResult, update_job_status,
    get_job, WebSocketMessage, job_storage
)

# Setup logging
logger = logging.getLogger(__name__)

class JobWorkerManager:
    """Manages background job processing"""

    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_jobs = set()
        self.websocket_connections: Dict[str, set] = {}  # job_id -> set of websocket connections

    def start_job(self, job_id: str) -> bool:
        """Start processing a job in the background"""
        job = get_job(job_id)
        if not job:
            logger.error(f"❌ Job {job_id} not found")
            return False

        if job_id in self.running_jobs:
            logger.warning(f"⚠️ Job {job_id} already running")
            return False

        # Mark job as running
        update_job_status(
            job_id,
            JobStatus.RUNNING,
            started_at=datetime.now()
        )

        self.running_jobs.add(job_id)

        # Submit job to thread pool
        future = self.executor.submit(self._process_job, job_id)

        # Handle completion callback
        future.add_done_callback(lambda f: self._job_completed(job_id, f))

        logger.info(f"🚀 Job {job_id} started in background")
        return True

    def _process_job(self, job_id: str):
        """Process job in background thread using real MatchTrex pipeline"""
        start_time = datetime.now()

        try:
            job = get_job(job_id)
            if not job:
                raise Exception(f"Job {job_id} not found")

            params = job["parameters"]

            logger.info(f"🔄 Processing job {job_id}")
            logger.info(f"   Keywords: {params['search_keywords']}")
            logger.info(f"   Location: {params.get('location', 'N/A')}")

            # Step 1: Initialize
            progress = JobProgress(
                step="initializing",
                progress_percent=5.0,
                candidates_found=0,
                current_action="Initializing search parameters...",
                estimated_completion=datetime.now() + timedelta(minutes=25)
            )
            update_job_status(job_id, JobStatus.RUNNING, progress=progress)
            self._broadcast_progress(job_id, {"status": "running", "progress": progress.dict()})

            # Import and run the real pipeline
            # We need to import here to avoid circular imports
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))

            # Import the main pipeline function from the same file (mvp.py)
            # We'll create a dedicated pipeline wrapper
            from pipeline_wrapper import run_pipeline_with_progress

            # Run the real pipeline with progress callbacks
            result_urls = run_pipeline_with_progress(
                job_id=job_id,
                search_keywords=params["search_keywords"],
                location=params.get("location"),
                resume_last_updated_days=params.get("resume_last_updated_days", 30),
                target_candidates=params.get("target_candidates", 100),
                max_radius=params.get("max_radius", 25),
                recipient_email=params["recipient_email"],
                user_prompt=params.get("user_prompt"),
                system_prompt=params.get("system_prompt"),
                progress_callback=self._update_pipeline_progress
            )

            # Job completed successfully
            processing_time = (datetime.now() - start_time).total_seconds() / 60

            result = JobResult(
                candidates=[{"url": url} for url in result_urls] if result_urls else [],
                total_found=len(result_urls) if result_urls else 0,
                qualified_count=len(result_urls) if result_urls else 0,
                summary={
                    "keywords": params["search_keywords"],
                    "location": params.get("location"),
                    "processing_time_minutes": round(processing_time, 2)
                },
                email_sent=True
            )

            update_job_status(
                job_id,
                JobStatus.COMPLETED,
                result=result,
                completed_at=datetime.now()
            )

            # Broadcast completion
            self._broadcast_progress(job_id, {
                "status": "completed",
                "result": result.dict()
            })

            logger.info(f"✅ Job {job_id} completed successfully")
            logger.info(f"   Found {result.qualified_count} qualified candidates")
            logger.info(f"   Processing time: {processing_time:.2f} minutes")

        except Exception as e:
            # Job failed
            error_msg = str(e)
            logger.error(f"❌ Job {job_id} failed: {error_msg}")

            update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=error_msg,
                completed_at=datetime.now()
            )

            # Broadcast failure
            self._broadcast_progress(job_id, {
                "status": "failed",
                "error": error_msg
            })

            raise  # Re-raise for thread pool error handling

    def _update_pipeline_progress(self, job_id: str, step: str, progress_percent: float,
                                candidates_found: int, current_action: str):
        """Callback function for pipeline progress updates"""
        progress = JobProgress(
            step=step,
            progress_percent=progress_percent,
            candidates_found=candidates_found,
            current_action=current_action,
            estimated_completion=datetime.now() + timedelta(minutes=max(1, (100-progress_percent)/4))
        )

        update_job_status(job_id, JobStatus.RUNNING, progress=progress)

        # Broadcast progress via WebSocket
        self._broadcast_progress(job_id, {
            "status": "running",
            "progress": progress.dict()
        })

        logger.info(f"📊 Job {job_id}: {step} ({progress_percent:.1f}%) - {current_action}")

    def _job_completed(self, job_id: str, future):
        """Callback when job completes (success or failure)"""
        self.running_jobs.discard(job_id)

        if future.exception():
            logger.error(f"💥 Job {job_id} thread failed: {future.exception()}")
        else:
            logger.info(f"🏁 Job {job_id} thread finished")

    def _broadcast_progress(self, job_id: str, data: Dict[str, Any]):
        """Broadcast progress to WebSocket connections (placeholder for now)"""
        message = WebSocketMessage(
            job_id=job_id,
            message_type="progress",
            data=data
        )

        # For now, just log the message
        # Later we'll implement actual WebSocket broadcasting
        logger.info(f"📡 Broadcasting to job {job_id}: {data.get('status', 'update')}")

    def add_websocket_connection(self, job_id: str, websocket):
        """Add WebSocket connection for job updates"""
        if job_id not in self.websocket_connections:
            self.websocket_connections[job_id] = set()
        self.websocket_connections[job_id].add(websocket)

    def remove_websocket_connection(self, job_id: str, websocket):
        """Remove WebSocket connection"""
        if job_id in self.websocket_connections:
            self.websocket_connections[job_id].discard(websocket)
            if not self.websocket_connections[job_id]:
                del self.websocket_connections[job_id]

    def get_running_jobs(self) -> set:
        """Get set of currently running job IDs"""
        return self.running_jobs.copy()

    def shutdown(self):
        """Gracefully shutdown the worker"""
        logger.info("🛑 Shutting down job worker...")
        self.executor.shutdown(wait=True)

# Global job worker instance
job_worker = JobWorkerManager(max_workers=2)

def start_job_processing(job_id: str) -> bool:
    """Public function to start job processing"""
    return job_worker.start_job(job_id)

def get_worker_status() -> Dict[str, Any]:
    """Get worker status for monitoring"""
    return {
        "max_workers": job_worker.max_workers,
        "running_jobs": list(job_worker.running_jobs),
        "active_connections": len(job_worker.websocket_connections)
    }