"""
Configuration file for MatchTrex application.
Contains settings for Google Sheets integration.
"""

# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH = "google_credentials.json"
GOOGLE_SHEETS_ID = "1_jqlLt0ckySKVJf2hED7fVJZamAA_kNdl1N6GTQcrFg"  # Replace with your actual Google Sheets document ID

# Default fallback configuration
DEFAULT_EXCEL_FILE = "SearchRecords.xlsx"  # Fallback to Excel if Google Sheets fails

# Data source priority: 'google_sheets' or 'excel'
DATA_SOURCE = 'google_sheets'  # Change to 'excel' to use Excel files instead

def get_google_sheets_id():
    """
    Get the Google Sheets ID from environment variable or config.
    Priority: Environment variable > config file setting
    """
    import os
    
    # Try to get from environment variable first
    sheets_id = os.environ.get('GOOGLE_SHEETS_ID')
    if sheets_id:
        return sheets_id
    
    # Fall back to config setting
    return GOOGLE_SHEETS_ID

def set_google_sheets_id(sheet_id):
    """
    Set the Google Sheets ID in the config.
    """
    global GOOGLE_SHEETS_ID
    GOOGLE_SHEETS_ID = sheet_id