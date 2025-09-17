#!/usr/bin/env python3
"""
Test script for Email Integration
Tests the complete email functionality with mock candidate data
"""
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the email function
from mvp import send_email_with_results

def test_email_integration():
    """Test email sending with realistic mock data"""
    print("🧪 Testing MatchTrex Email Integration")
    print("=" * 50)

    # Mock qualified candidates (with the structure expected by email function)
    mock_candidates = [
        {
            'name': 'Dr. Stefan Müller',
            'location': 'Berlin, Deutschland',
            'url': 'https://resumes.indeed.com/resume/demo1',
            'ai_response': 'Hervorragender Senior Full-Stack Developer mit 8+ Jahren Erfahrung. Expertise in React, Node.js, Python und AWS. Führungserfahrung als Team-Lead für 5 Entwickler. Perfekte Passung für die Anforderungen.'
        },
        {
            'name': 'Anna Schmidt',
            'location': 'Hamburg, Deutschland',
            'url': 'https://resumes.indeed.com/resume/demo2',
            'ai_response': 'Starke Frontend-Spezialistin mit Fokus auf moderne JavaScript-Frameworks. Umfangreiche Erfahrung mit React und Vue.js. Sehr gutes UX/UI Verständnis. Würde gut ins Team passen.'
        },
        {
            'name': 'Michael Weber',
            'location': 'München, Deutschland',
            'url': 'https://resumes.indeed.com/resume/demo3',
            'ai_response': 'Erfahrener Backend-Entwickler mit Python und Django Expertise. Cloud-Kenntnisse mit AWS und Docker. Agile Arbeitsweise und Code Review Erfahrung.'
        }
    ]

    # Test parameters
    search_keywords = "Senior Entwickler"
    location = "Berlin"
    radius = 50
    recipient_email = "ndricim@beyondleverage.com"
    search_name = "Demo Search - Senior Entwickler Berlin"

    print(f"Test Configuration:")
    print(f"   Search Name: {search_name}")
    print(f"   Keywords: {search_keywords}")
    print(f"   Location: {location} ({radius}km radius)")
    print(f"   Recipients: {recipient_email}")
    print(f"   Mock Candidates: {len(mock_candidates)}")
    print()

    try:
        print("📧 Sending test email...")
        send_email_with_results(
            mock_candidates,
            search_keywords,
            location,
            radius,
            recipient_email,
            search_name
        )

        print("✅ Email Integration Test SUCCESSFUL!")
        print()
        print("📋 Email should contain:")
        print("   • Professional HTML layout with MatchTrex branding")
        print("   • 3 candidate profiles with names and locations")
        print("   • KI-Bewertung for each candidate")
        print("   • Clickable links to profile URLs")
        print("   • Search parameters summary")
        print("   • Professional footer with timestamp")
        print()
        print("🎯 Check your email inbox to verify the result!")

    except Exception as e:
        print(f"❌ Email Integration Test FAILED: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   • Check EMAIL_USER and EMAIL_PASS in .env file")
        print("   • Verify SMTP_SERVER and SMTP_PORT settings")
        print("   • Ensure email credentials are correct")
        print("   • Check internet connection")

def test_email_with_real_search():
    """Test email with data from a real Supabase search"""
    print("\n" + "=" * 50)
    print("🔗 Testing Email with Real Supabase Search Data")
    print("=" * 50)

    try:
        # Import Supabase functions
        from supabase_client import load_search_from_supabase

        # Load real search
        search_id = "caa7f9b0-1e52-424b-9d56-f26a355a00cd"
        search_data = load_search_from_supabase(search_id)

        if not search_data:
            print(f"❌ Could not load search {search_id}")
            return

        print(f"✅ Loaded real search: {search_data.get('name', 'Unnamed')}")

        # Use the same mock candidates but with real search data
        mock_candidates = [
            {
                'name': 'Test Kandidat 1',
                'location': 'Berlin, Deutschland',
                'url': 'https://resumes.indeed.com/resume/test1',
                'ai_response': 'Demo: Dieser Kandidat würde die Anforderungen erfüllen. Test mit echten Supabase-Daten.'
            }
        ]

        print("📧 Sending email with real search parameters...")
        send_email_with_results(
            mock_candidates,
            search_data.get('search_keywords', 'Test'),
            search_data.get('location', 'Berlin'),
            search_data.get('max_radius', 25),
            search_data.get('recipient_email', 'ndricim@beyondleverage.com'),
            search_data.get('name', 'Test Search')
        )

        print("✅ Real Search Email Test SUCCESSFUL!")

    except Exception as e:
        print(f"❌ Real Search Email Test FAILED: {e}")

if __name__ == "__main__":
    test_email_integration()
    test_email_with_real_search()