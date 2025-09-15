"""
Supabase Service for MatchTrex Job Persistence
Handles database operations for job storage and retrieval
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from supabase import create_client, Client

# Setup logging
logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for Supabase database operations"""

    def __init__(self):
        # Get Supabase credentials from environment
        supabase_url = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
        supabase_key = os.getenv("SUPABASE_ANON_KEY", "your_anon_key")

        if not supabase_url or supabase_url == "https://your-project.supabase.co":
            logger.warning("⚠️ SUPABASE_URL not configured - using in-memory storage only")
            self.client = None
            return

        if not supabase_key or supabase_key == "your_anon_key":
            logger.warning("⚠️ SUPABASE_ANON_KEY not configured - using in-memory storage only")
            self.client = None
            return

        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Supabase is available and configured"""
        return self.client is not None

    def save_job(self, job_data: Dict[str, Any]) -> bool:
        """Save job to Supabase searches table"""
        if not self.is_available():
            logger.debug("Supabase not available - skipping database save")
            return False

        try:
            # Map job data to searches table schema
            search_data = {
                "name": f"Job {job_data['job_id'][:8]}",
                "search_keywords": job_data["parameters"]["search_keywords"],
                "location": job_data["parameters"].get("location"),
                "resume_last_updated_days": job_data["parameters"].get("resume_last_updated_days"),
                "target_candidates": job_data["parameters"].get("target_candidates"),
                "max_radius": job_data["parameters"].get("max_radius"),
                "recipient_email": job_data["parameters"].get("recipient_email"),
                "user_prompt": job_data["parameters"].get("user_prompt"),
                "system_prompt": job_data["parameters"].get("system_prompt"),
                "status": job_data["status"].value if hasattr(job_data["status"], 'value') else str(job_data["status"]),
                "results": job_data.get("result", {}) if job_data.get("result") else None,
                "filters": {
                    "job_id": job_data["job_id"],
                    "async_job": True,
                    "created_via_api": True
                },
                "created_at": job_data["created_at"].isoformat() if job_data.get("created_at") else None,
                "completed_at": job_data["completed_at"].isoformat() if job_data.get("completed_at") else None
            }

            # Insert into searches table
            result = self.client.table("searches").insert(search_data).execute()

            if result.data:
                logger.info(f"✅ Job {job_data['job_id']} saved to Supabase")
                return True
            else:
                logger.error(f"❌ Failed to save job {job_data['job_id']} to Supabase")
                return False

        except Exception as e:
            logger.error(f"❌ Error saving job to Supabase: {e}")
            return False

    def update_job_status(self, job_id: str, status: str, progress: Optional[Dict] = None,
                         result: Optional[Dict] = None, error_message: Optional[str] = None,
                         completed_at: Optional[datetime] = None) -> bool:
        """Update job status in Supabase"""
        if not self.is_available():
            logger.debug("Supabase not available - skipping database update")
            return False

        try:
            # Find the job by job_id in filters
            search_result = self.client.table("searches").select("*").eq("filters->>job_id", job_id).execute()

            if not search_result.data:
                logger.warning(f"⚠️ Job {job_id} not found in Supabase for update")
                return False

            search_id = search_result.data[0]["id"]

            # Prepare update data
            update_data = {
                "status": status
            }

            if result:
                update_data["results"] = result

            if completed_at:
                update_data["completed_at"] = completed_at.isoformat()

            if error_message:
                # Store error in filters
                current_filters = search_result.data[0].get("filters", {})
                current_filters["error_message"] = error_message
                update_data["filters"] = current_filters

            if progress:
                # Store progress in filters
                current_filters = search_result.data[0].get("filters", {})
                current_filters["progress"] = progress
                update_data["filters"] = current_filters

            # Update the record
            result = self.client.table("searches").update(update_data).eq("id", search_id).execute()

            if result.data:
                logger.info(f"✅ Job {job_id} status updated to {status} in Supabase")
                return True
            else:
                logger.error(f"❌ Failed to update job {job_id} status in Supabase")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating job status in Supabase: {e}")
            return False

    def get_job_from_database(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job from Supabase by job_id"""
        if not self.is_available():
            return None

        try:
            result = self.client.table("searches").select("*").eq("filters->>job_id", job_id).execute()

            if result.data:
                search_data = result.data[0]
                logger.info(f"✅ Retrieved job {job_id} from Supabase")

                # Map back to job format
                return {
                    "job_id": job_id,
                    "status": search_data["status"],
                    "created_at": datetime.fromisoformat(search_data["created_at"].replace("Z", "+00:00")),
                    "completed_at": datetime.fromisoformat(search_data["completed_at"].replace("Z", "+00:00")) if search_data.get("completed_at") else None,
                    "result": search_data.get("results"),
                    "progress": search_data.get("filters", {}).get("progress"),
                    "error_message": search_data.get("filters", {}).get("error_message"),
                    "parameters": {
                        "search_keywords": search_data["search_keywords"],
                        "location": search_data["location"],
                        "resume_last_updated_days": search_data["resume_last_updated_days"],
                        "target_candidates": search_data["target_candidates"],
                        "max_radius": search_data["max_radius"],
                        "recipient_email": search_data["recipient_email"],
                        "user_prompt": search_data["user_prompt"],
                        "system_prompt": search_data["system_prompt"]
                    }
                }
            else:
                logger.warning(f"⚠️ Job {job_id} not found in Supabase")
                return None

        except Exception as e:
            logger.error(f"❌ Error retrieving job from Supabase: {e}")
            return None

    def get_recent_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent async jobs from Supabase"""
        if not self.is_available():
            return []

        try:
            result = self.client.table("searches").select("*").eq("filters->>async_job", "true").order("created_at", desc=True).limit(limit).execute()

            jobs = []
            for search_data in result.data:
                job_id = search_data.get("filters", {}).get("job_id", "unknown")
                jobs.append({
                    "job_id": job_id,
                    "status": search_data["status"],
                    "created_at": search_data["created_at"],
                    "completed_at": search_data.get("completed_at"),
                    "search_keywords": search_data["search_keywords"],
                    "location": search_data["location"],
                    "qualified_count": len(search_data.get("results", {}).get("candidates", [])) if search_data.get("results") else 0
                })

            logger.info(f"✅ Retrieved {len(jobs)} recent jobs from Supabase")
            return jobs

        except Exception as e:
            logger.error(f"❌ Error retrieving recent jobs from Supabase: {e}")
            return []

    def test_connection(self) -> Dict[str, Any]:
        """Test Supabase connection"""
        if not self.is_available():
            return {"status": "unavailable", "reason": "Client not initialized"}

        try:
            # Try to query searches table
            result = self.client.table("searches").select("id").limit(1).execute()
            return {
                "status": "connected",
                "message": "Successfully connected to Supabase",
                "table_accessible": True
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "table_accessible": False
            }

# Global instance
supabase_service = SupabaseService()