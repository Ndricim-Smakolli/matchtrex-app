"""
John Doe detection and handling utilities
"""

import json
import time
from cookie_refresher import get_fresh_headers

def detect_john_doe_response(response_data):
    """
    Detect if Indeed API returned fake/placeholder data
    """
    if not response_data or not isinstance(response_data, dict):
        return True
    
    # Check if response contains actual data
    try:
        matches = response_data.get('data', {}).get('findRCPMatches', {}).get('matchConnection', {}).get('matches', [])
        
        if not matches:
            return True
            
        # Check for placeholder names
        john_doe_indicators = ['john doe', 'jane doe', 'test user', 'sample user', 'placeholder']
        
        for match in matches:
            profile_card = match.get('sourcingProfile', {}).get('profileCard', {})
            first_name = profile_card.get('firstName', '').lower()
            last_name = profile_card.get('lastName', '').lower()
            
            full_name = f"{first_name} {last_name}".strip()
            
            # Check for placeholder names
            if any(indicator in full_name for indicator in john_doe_indicators):
                return True
                
            # Check for generic/empty data
            if not first_name or not last_name or first_name == 'not found' or last_name == 'not found':
                return True
                
        return False
        
    except (KeyError, TypeError):
        return True

def handle_john_doe_response(make_request_func, *args, **kwargs):
    """
    Handle John Doe responses by retrying with fresh authentication
    """
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        print(f"🔍 Attempt {retry_count + 1}/{max_retries}")
        
        # Make the request
        response = make_request_func(*args, **kwargs)
        
        if response and not detect_john_doe_response(response):
            print("✅ Valid candidate data received")
            return response
        
        print("⚠️  John Doe / placeholder data detected")
        
        if retry_count < max_retries - 1:
            print("🔄 Refreshing authentication and retrying...")
            
            # Get fresh headers
            fresh_headers = get_fresh_headers()
            
            if fresh_headers:
                # Update the headers in the request function
                # This would need to be implemented in the calling function
                print("🔑 Fresh authentication obtained")
                time.sleep(2)  # Brief delay
            else:
                print("❌ Failed to refresh authentication")
                time.sleep(5)  # Longer delay before retry
        
        retry_count += 1
    
    print("❌ All retries exhausted, returning last response")
    return response

def validate_candidate_data(candidates):
    """
    Validate that candidate data is real and not placeholder
    """
    if not candidates:
        return False, "No candidates returned"
    
    real_candidates = 0
    issues = []
    
    for i, candidate in enumerate(candidates):
        first_name = candidate.get('firstName', '').lower()
        last_name = candidate.get('lastName', '').lower()
        
        # Check for placeholder names
        if 'john doe' in f"{first_name} {last_name}":
            issues.append(f"Candidate {i+1}: John Doe detected")
            continue
            
        # Check for missing data
        if not first_name or not last_name or first_name == 'not found':
            issues.append(f"Candidate {i+1}: Missing name data")
            continue
            
        # Check for realistic experience data
        experiences = candidate.get('experiences', [])
        if not experiences or experiences == 'not found':
            issues.append(f"Candidate {i+1}: No experience data")
            continue
            
        real_candidates += 1
    
    success_rate = real_candidates / len(candidates) * 100
    
    if success_rate < 50:
        return False, f"Only {success_rate:.1f}% real candidates. Issues: {issues[:5]}"
    
    return True, f"✅ {success_rate:.1f}% real candidates ({real_candidates}/{len(candidates)})"

if __name__ == "__main__":
    # Test detection
    test_data = {
        'data': {
            'findRCPMatches': {
                'matchConnection': {
                    'matches': [
                        {
                            'sourcingProfile': {
                                'profileCard': {
                                    'firstName': 'John',
                                    'lastName': 'Doe',
                                    'experiences': []
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
    
    is_fake = detect_john_doe_response(test_data)
    print(f"John Doe detected: {is_fake}")