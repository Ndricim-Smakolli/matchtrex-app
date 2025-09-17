#!/usr/bin/env python3
"""
Test script to debug CV extraction with MistralAI
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the extraction function
from mvp import extract_cv_data_with_mistral

def test_cv_extraction():
    """Test CV extraction on saved CV files"""
    cv_files = [
        "temp_CVs/cv_1a7b8b37a2f325cd.html",
        "temp_CVs/cv_89772890fd7fd0ba.html"
    ]

    for cv_file in cv_files:
        if os.path.exists(cv_file):
            print(f"\n=== Testing {cv_file} ===")

            # Read HTML content
            with open(cv_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            print(f"HTML length: {len(html_content)} characters")

            # Test extraction
            result = extract_cv_data_with_mistral(html_content)

            if result:
                print(f"✅ Extraction successful!")
                print(f"   Name: {result.get('name', 'Missing')}")
                print(f"   Email: {result.get('email', 'Missing')}")
                print(f"   Location: {result.get('location', 'Missing')}")
                print(f"   All fields: {list(result.keys())}")
            else:
                print(f"❌ Extraction failed - No data returned")
        else:
            print(f"❌ File not found: {cv_file}")

if __name__ == "__main__":
    test_cv_extraction()