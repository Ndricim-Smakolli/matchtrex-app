#!/usr/bin/env python3
"""
Direct test of the pipeline to check if it works
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the pipeline function
from supabase_client import load_search_from_supabase
from mvp import main_pipeline_for_api

async def test_pipeline():
    """Test the pipeline directly"""
    try:
        # Load search data
        search_id = "caa7f9b0-1e52-424b-9d56-f26a355a00cd"
        search_data = load_search_from_supabase(search_id)

        if not search_data:
            print(f"❌ Could not load search data for {search_id}")
            return

        print(f"✅ Loaded search: {search_data.get('name', 'Unnamed')}")
        print(f"   Keywords: {search_data.get('search_keywords')}")
        print(f"   User prompt: {search_data.get('user_prompt', 'None')[:100]}...")
        print(f"   System prompt: {search_data.get('system_prompt', 'None')[:100]}...")

        # Run pipeline
        print("🚀 Starting pipeline...")
        results = await asyncio.get_event_loop().run_in_executor(
            None, main_pipeline_for_api, search_data
        )

        print(f"✅ Pipeline completed!")
        print(f"   Results: {results}")

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())