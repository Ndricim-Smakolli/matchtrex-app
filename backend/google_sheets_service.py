import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

class GoogleSheetsService:
    """
    Service class for Google Sheets integration to replace Excel functionality.
    """
    
    def __init__(self, credentials_path="google_credentials.json", sheet_id=None):
        """
        Initialize Google Sheets service.
        
        Args:
            credentials_path (str): Path to Google service account credentials JSON file
            sheet_id (str): Google Sheets document ID
        """
        self.credentials_path = credentials_path
        self.sheet_id = sheet_id
        self.client = None
        self.spreadsheet = None
        
    def setup_authentication(self):
        """
        Set up Google Sheets authentication using service account credentials.
        """
        try:
            # Define the scope for Google Sheets API
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Load credentials from JSON file
            if not os.path.exists(self.credentials_path):
                print(f"❌ Google credentials file not found: {self.credentials_path}")
                print("Please create a service account and download the credentials JSON file.")
                return False
            
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scope
            )
            
            # Create the client
            self.client = gspread.authorize(credentials)
            print("✅ Google Sheets authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Google Sheets authentication: {e}")
            return False
    
    def open_spreadsheet(self, sheet_id=None):
        """
        Open the Google Sheets document.
        
        Args:
            sheet_id (str): Google Sheets document ID (optional if set in init)
        """
        try:
            if sheet_id:
                self.sheet_id = sheet_id
                
            if not self.sheet_id:
                print("❌ No Google Sheets ID provided")
                return False
                
            if not self.client:
                print("❌ Google Sheets client not authenticated")
                return False
                
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            print(f"✅ Successfully opened Google Sheets document: {self.spreadsheet.title}")
            return True
            
        except Exception as e:
            print(f"❌ Error opening Google Sheets document: {e}")
            return False
    
    def read_search_parameters(self):
        """
        Read search parameters from Google Sheets 'Search Parameters' sheet.
        Returns a dictionary with all search parameters.
        """
        try:
            if not self.spreadsheet:
                print("❌ No spreadsheet opened")
                return {}
            
            # Try to get the 'Search Parameters' worksheet
            try:
                worksheet = self.spreadsheet.worksheet("Search Parameters")
            except gspread.WorksheetNotFound:
                print("'Search Parameters' sheet not found. Creating with default parameters...")
                self.create_default_search_parameters_sheet()
                worksheet = self.spreadsheet.worksheet("Search Parameters")
            
            # Get all values from the sheet
            values = worksheet.get_all_values()
            
            if len(values) < 2:  # Need at least header + 1 data row
                print("No data found in Search Parameters sheet")
                return self.get_default_parameters()
            
            # Parse parameters (assuming format: Parameter Name | Value | Description)
            parameters = {}
            for row in values[1:]:  # Skip header row
                if len(row) >= 2 and row[0] and row[1]:  # Both parameter name and value exist
                    param_name = str(row[0]).strip()
                    param_value = row[1]
                    
                    # Try to convert numeric values
                    if param_value.isdigit():
                        param_value = int(param_value)
                    
                    parameters[param_name] = param_value
            
            print(f"✅ Successfully read {len(parameters)} search parameters from Google Sheets")
            return parameters
            
        except Exception as e:
            print(f"❌ Error reading search parameters from Google Sheets: {e}")
            print("Using default hardcoded parameters...")
            return self.get_default_parameters()
    
    def create_default_search_parameters_sheet(self):
        """
        Create a default 'Search Parameters' sheet with all configurable parameters.
        """
        try:
            # Check if sheet already exists
            try:
                worksheet = self.spreadsheet.worksheet("Search Parameters")
                # Clear existing content
                worksheet.clear()
            except gspread.WorksheetNotFound:
                # Create new sheet
                worksheet = self.spreadsheet.add_worksheet(title="Search Parameters", rows=20, cols=3)
            
            # Add headers
            headers = ["Parameter Name", "Value", "Description"]
            worksheet.update('A1:C1', [headers])
            
            # Add default parameters
            default_params = [
                ["search_keywords", "Verkäufer or Verkäuferin or salesperson or Einzelhandel or Verkauf or kaufmann or kauffrau or verkaufsberater or kundenberater or verkaufsberaterin or kundenberaterin", "Keywords to search for candidates"],
                ["location", "Buxtehude", "Search location"],
                ["resume_last_updated_days", "30", "Filter profiles updated within X days"],
                ["target_candidates", "100", "Minimum candidates to find before stopping"],
                ["max_radius", "50", "Maximum search radius in km"],
                ["recipient_email", "parth@beyondleverage.com", "Email recipient for results"],
                ["user_prompt", "EVALUATE each candidate against these EXACT criteria:\n\nCRITERION 1 - Experience Duration:\nPASS: Based on the experience provided, the candidate should have atleast 4+ years total professional experience (This is a non-negotiable requirement)\nFAIL: Less than 4 years total experience\n\nCRITERION 2 - Job Stability:\nPASS: 0-1 positions shorter than 6 months in last 2 years (2023-2025)\nFAIL: 2+ positions shorter than 6 months in last 2 years\n\nCRITERION 3 - Consultative Sales Experience:\nPASS: 1+ year in advisory/consultative sales roles:\n  - Fashion retail with customer styling/advice\n  - Furniture sales with design consultation\n  - Pet supplies with animal care advice\n  - Optics/eyewear with vision consultation\n  - Electronics with technical consultation\n  - Similar customer advisory positions\n\nFAIL: Only cashier, warehouse, or basic sales without consultation\n\nREQUIRED OUTPUT FORMAT:\n[\"https://resumes.indeed.com/resume/abc123\", \"https://resumes.indeed.com/resume/def456\"]\n\nIF NO CANDIDATES QUALIFY:\n[]\n\nNo SUMMARY. NO EXPLANATION. ANALYZE AND RETURN ONLY JSON ARRAY NOW:", "User prompt for MistralAI candidate evaluation"],
                ["system_prompt", "You are an experienced recruiter specializing in fashion retail sales positions. Your task is to evaluate candidate CVs against specific criteria and return only the profile URLs of candidates who meet ALL requirements.", "System prompt for MistralAI"]
            ]
            
            # Update the sheet with default parameters
            worksheet.update(f'A2:C{len(default_params) + 1}', default_params)
            
            print("✅ Default search parameters sheet created in Google Sheets")
            
        except Exception as e:
            print(f"❌ Error creating default search parameters sheet: {e}")
    
    def log_search_to_sheet(self, search_id, keywords, location, radius, user_prompt="", system_prompt=""):
        """
        Log search details to Google Sheets 'Search History' sheet.
        """
        try:
            if not self.spreadsheet:
                print("❌ No spreadsheet opened")
                return False
            
            # Try to get the 'Search History' worksheet
            try:
                worksheet = self.spreadsheet.worksheet("Search History")
            except gspread.WorksheetNotFound:
                # Create new sheet
                worksheet = self.spreadsheet.add_worksheet(title="Search History", rows=100, cols=6)
                # Add headers
                headers = ["SearchID", "Keywords", "Location", "Radius", "User Prompt", "System Prompt"]
                worksheet.update('A1:F1', [headers])
            
            # Find the next empty row
            values = worksheet.get_all_values()
            next_row = len(values) + 1
            
            # Add search data
            search_data = [search_id, keywords, location, radius, user_prompt, system_prompt]
            worksheet.update(f'A{next_row}:F{next_row}', [search_data])
            
            print(f"✅ Search logged to Google Sheets: {search_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error logging to Google Sheets: {e}")
            return False
    
    def get_default_parameters(self):
        """
        Return default parameters as fallback.
        """
        return {
            "search_keywords": "Verkäufer or Verkäuferin or salesperson or Einzelhandel or Verkauf or kaufmann or kauffrau or verkaufsberater or kundenberater or verkaufsberaterin or kundenberaterin",
            "location": "Buxtehude",
            "resume_last_updated_days": 30,
            "target_candidates": 100,
            "max_radius": 50,
            "recipient_email": "parth@beyondleverage.com",
            "user_prompt": "EVALUATE each candidate against these EXACT criteria:\n\nCRITERION 1 - Experience Duration:\nPASS: Based on the experience provided, the candidate should have atleast 4+ years total professional experience (This is a non-negotiable requirement)\nFAIL: Less than 4 years total experience\n\nCRITERION 2 - Job Stability:\nPASS: 0-1 positions shorter than 6 months in last 2 years (2023-2025)\nFAIL: 2+ positions shorter than 6 months in last 2 years\n\nCRITERION 3 - Consultative Sales Experience:\nPASS: 1+ year in advisory/consultative sales roles:\n  - Fashion retail with customer styling/advice\n  - Furniture sales with design consultation\n  - Pet supplies with animal care advice\n  - Optics/eyewear with vision consultation\n  - Electronics with technical consultation\n  - Similar customer advisory positions\n\nFAIL: Only cashier, warehouse, or basic sales without consultation\n\nREQUIRED OUTPUT FORMAT:\n[\"https://resumes.indeed.com/resume/abc123\", \"https://resumes.indeed.com/resume/def456\"]\n\nIF NO CANDIDATES QUALIFY:\n[]\n\nNo SUMMARY. NO EXPLANATION. ANALYZE AND RETURN ONLY JSON ARRAY NOW:",
            "system_prompt": "You are an experienced recruiter specializing in fashion retail sales positions. Your task is to evaluate candidate CVs against specific criteria and return only the profile URLs of candidates who meet ALL requirements."
        }

# Helper functions for backward compatibility
def read_search_parameters_from_google_sheets(credentials_path="google_credentials.json", sheet_id=None):
    """
    Helper function to read search parameters from Google Sheets.
    Replaces the Excel-based function.
    """
    if not sheet_id:
        print("❌ Google Sheets ID not provided")
        return {}
    
    gs_service = GoogleSheetsService(credentials_path, sheet_id)
    
    if not gs_service.setup_authentication():
        return {}
    
    if not gs_service.open_spreadsheet():
        return {}
    
    return gs_service.read_search_parameters()

def log_search_to_google_sheets(search_id, keywords, location, radius, user_prompt="", system_prompt="", 
                               credentials_path="google_credentials.json", sheet_id=None):
    """
    Helper function to log search to Google Sheets.
    Replaces the Excel-based function.
    """
    if not sheet_id:
        print("❌ Google Sheets ID not provided")
        return False
    
    gs_service = GoogleSheetsService(credentials_path, sheet_id)
    
    if not gs_service.setup_authentication():
        return False
    
    if not gs_service.open_spreadsheet():
        return False
    
    return gs_service.log_search_to_sheet(search_id, keywords, location, radius, user_prompt, system_prompt)