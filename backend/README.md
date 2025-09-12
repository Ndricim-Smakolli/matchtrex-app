# MatchTrex Google Sheets Integration

This project has been updated to use Google Sheets instead of Excel files for configuration management.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Google Sheets Setup
1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Sheets API

2. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Download the JSON credentials file
   - Rename it to `google_credentials.json` and place in project root

3. **Create Google Sheets Document**:
   - Create a new Google Sheets document
   - Share it with the service account email (found in the JSON file)
   - Give "Editor" permissions
   - Copy the document ID from the URL

4. **Configure the Application**:
   - Edit `config.py` and set `GOOGLE_SHEETS_ID = "your_sheet_id"`
   - Or set environment variable: `export GOOGLE_SHEETS_ID="your_sheet_id"`

### 3. Run the Application
```bash
python main.py
```

## Configuration Options

### Data Source Priority
The system will try Google Sheets first, then fall back to Excel if needed:

- **Google Sheets (Primary)**: Set `DATA_SOURCE = 'google_sheets'` in `config.py`
- **Excel (Fallback)**: Set `DATA_SOURCE = 'excel'` in `config.py`

### Sheet Structure
The system creates two sheets automatically:

1. **Search Parameters**: Configuration values for searches
2. **Search History**: Log of all searches with unique IDs

### Fallback Behavior
- If Google Sheets is unavailable, the system automatically falls back to Excel
- If credentials are missing, it will use Excel files
- If Google Sheets ID is not configured, it will use Excel files

## Files Overview

- `main.py`: Main application (updated to use Google Sheets)
- `google_sheets_service.py`: Google Sheets integration service
- `config.py`: Configuration settings
- `requirements.txt`: Updated dependencies
- `google_credentials.json`: Google service account credentials (you need to create this)

## Migration from Excel

Your existing Excel files will continue to work as fallback. The system will automatically create Google Sheets with the same structure and data.

## Troubleshooting

1. **Authentication Error**: Make sure `google_credentials.json` is in the project root
2. **Permission Error**: Ensure the Google Sheets document is shared with the service account email
3. **Sheet Not Found**: The system will create missing sheets automatically
4. **API Limits**: Google Sheets API has usage limits; the system will fall back to Excel if needed

## Environment Variables

You can set these environment variables instead of editing `config.py`:

```bash
export GOOGLE_SHEETS_ID="your_sheet_id_here"
```

This allows you to keep sensitive information out of your code.