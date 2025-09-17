"""
Supabase Client for MatchTrex Backend
Handles all database operations for search management
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Warning: SUPABASE_URL and SUPABASE_KEY environment variables not set")
    print("   Using fallback values for local development")
    # For now, we'll use None and catch errors gracefully
    supabase: Optional[Client] = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        supabase = None

def get_supabase_client() -> Optional[Client]:
    """Get the Supabase client instance"""
    return supabase

def load_search_from_supabase(search_id: str) -> Optional[Dict]:
    """Load search data from Supabase by ID"""
    if not supabase:
        print("❌ Supabase client not available")
        return None

    try:
        response = supabase.table('searches').select('*').eq('id', search_id).execute()
        if response.data and len(response.data) > 0:
            print(f"✅ Loaded search {search_id} from Supabase")
            return response.data[0]
        else:
            print(f"❌ Search {search_id} not found in Supabase")
            return None
    except Exception as e:
        print(f"❌ Error loading search {search_id}: {e}")
        return None

def update_search_status(search_id: str, status: str, progress: str = None, error: str = None) -> bool:
    """Update search status in Supabase"""
    if not supabase:
        print(f"❌ Supabase client not available - would update {search_id} to {status}")
        return False

    try:
        update_data = {'status': status}

        if progress:
            update_data['progress'] = progress

        if error:
            update_data['error'] = error

        if status == 'completed':
            update_data['completed_at'] = datetime.now().isoformat()

        response = supabase.table('searches').update(update_data).eq('id', search_id).execute()
        print(f"✅ Updated search {search_id} status to '{status}'")
        return True

    except Exception as e:
        print(f"❌ Error updating search {search_id} status: {e}")
        return False

def update_search_results(search_id: str, results: Dict) -> bool:
    """Update search results in Supabase"""
    if not supabase:
        print(f"❌ Supabase client not available - would update {search_id} with results")
        return False

    try:
        update_data = {
            'results': results,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }

        response = supabase.table('searches').update(update_data).eq('id', search_id).execute()
        print(f"✅ Updated search {search_id} with results")
        return True

    except Exception as e:
        print(f"❌ Error updating search {search_id} results: {e}")
        return False

def mark_search_failed(search_id: str, error_message: str) -> bool:
    """Mark search as failed with error message"""
    if not supabase:
        print(f"❌ Supabase client not available - would mark {search_id} as failed: {error_message}")
        return False

    try:
        update_data = {
            'status': 'failed',
            'error': error_message,
            'completed_at': datetime.now().isoformat()
        }

        response = supabase.table('searches').update(update_data).eq('id', search_id).execute()
        print(f"✅ Marked search {search_id} as failed: {error_message}")
        return True

    except Exception as e:
        print(f"❌ Error marking search {search_id} as failed: {e}")
        return False

# Test function for debugging
def test_supabase_connection():
    """Test the Supabase connection"""
    if not supabase:
        print("❌ No Supabase client available")
        return False

    try:
        # Try to query the searches table
        response = supabase.table('searches').select('id').limit(1).execute()
        print("✅ Supabase connection test successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection test failed: {e}")
        return False