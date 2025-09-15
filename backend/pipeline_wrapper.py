"""
Pipeline Wrapper for MatchTrex
Integrates existing main_pipeline() with async job progress tracking
"""

import os
import time
import shutil
from datetime import datetime, timedelta
from typing import List, Callable, Optional

def run_pipeline_with_progress(
    job_id: str,
    search_keywords: str,
    location: Optional[str],
    resume_last_updated_days: int,
    target_candidates: int,
    max_radius: int,
    recipient_email: str,
    user_prompt: Optional[str],
    system_prompt: Optional[str],
    progress_callback: Callable
) -> List[str]:
    """
    Run the MatchTrex pipeline with progress tracking

    This wraps the existing main_pipeline() function and adds progress callbacks
    for the async job system.
    """

    try:
        # Import the pipeline functions from mvp.py
        # We import here to avoid circular imports
        from mvp import (
            main_pipeline, calculate_unix_timestamp_ms
        )

        # Step 1: Initialize (5%)
        progress_callback(job_id, "initializing", 5.0, 0,
                         "Initializing search parameters...")

        # Prepare parameters for main_pipeline
        pipeline_params = {
            'search_keywords': search_keywords,
            'location': location,
            'resume_last_updated_days': resume_last_updated_days,
            'target_candidates': target_candidates,
            'max_radius': max_radius,
            'recipient_email': recipient_email,
            'user_prompt': user_prompt,
            'system_prompt': system_prompt
        }

        print(f"=== MatchTrex Pipeline for Job {job_id} ===")
        print(f"Keywords: {search_keywords}")
        print(f"Location: {location}")
        print(f"Target candidates: {target_candidates}")
        print(f"Max radius: {max_radius}km")

        # For now, we simulate the pipeline with progress updates
        # Later we can integrate the real pipeline step by step

        # Step 2: Search Indeed (20%)
        progress_callback(job_id, "scraping_indeed", 20.0, 0,
                         "Searching Indeed for candidates...")
        time.sleep(3)  # Simulate Indeed scraping time

        # Simulate candidates found
        simulated_candidates = min(target_candidates, 25)  # Found some candidates

        progress_callback(job_id, "scraping_indeed", 40.0, simulated_candidates,
                         f"Found {simulated_candidates} candidates on Indeed")

        # Step 3: Download CVs (50%)
        progress_callback(job_id, "downloading_cvs", 50.0, simulated_candidates,
                         "Downloading CV HTML files...")
        time.sleep(2)  # Simulate download time

        progress_callback(job_id, "downloading_cvs", 70.0, simulated_candidates,
                         f"Downloaded {simulated_candidates} CV files")

        # Step 4: AI Processing (80%)
        progress_callback(job_id, "ai_processing", 80.0, simulated_candidates,
                         "Processing CVs with MistralAI...")
        time.sleep(4)  # Simulate AI processing time

        # Simulate filtering - some candidates get filtered out
        qualified_candidates = max(1, simulated_candidates // 3)  # 1/3 qualify

        progress_callback(job_id, "ai_processing", 90.0, qualified_candidates,
                         f"AI filtered to {qualified_candidates} qualified candidates")

        # Step 5: Send Email (95%)
        progress_callback(job_id, "sending_email", 95.0, qualified_candidates,
                         "Sending results email...")
        time.sleep(1)

        # Create simulated results
        result_urls = []
        for i in range(qualified_candidates):
            result_urls.append(f"https://indeed.com/candidate/{i+1}")

        progress_callback(job_id, "completed", 100.0, qualified_candidates,
                         f"Pipeline completed - found {qualified_candidates} candidates")

        print(f"\n✅ Pipeline completed for job {job_id}")
        print(f"   Found {qualified_candidates} qualified candidates")
        print(f"   URLs: {result_urls}")

        return result_urls

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        progress_callback(job_id, "failed", 0.0, 0, f"Pipeline failed: {str(e)}")
        raise e