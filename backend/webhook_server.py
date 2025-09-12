"""
Webhook server to receive triggers from Google Sheets and run mvp.py
"""

import subprocess
import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
from google_sheets_service import GoogleSheetsService
from config import get_google_sheets_id, GOOGLE_SHEETS_CREDENTIALS_PATH

app = Flask(__name__)

# Configuration
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'mvp.py')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'webhook_logs.txt')

def log_message(message):
    """Log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"Error writing to log file: {e}")

def update_sheet_status(status, message):
    """Update status in Google Sheets"""
    try:
        sheet_id = get_google_sheets_id()
        if not sheet_id:
            log_message("No Google Sheets ID configured for status update")
            return
        
        gs_service = GoogleSheetsService(GOOGLE_SHEETS_CREDENTIALS_PATH, sheet_id)
        
        if not gs_service.setup_authentication():
            log_message("Failed to authenticate for status update")
            return
        
        if not gs_service.open_spreadsheet():
            log_message("Failed to open spreadsheet for status update")
            return
        
        # Get the Search Parameters sheet
        try:
            worksheet = gs_service.spreadsheet.worksheet("Search Parameters")
        except:
            log_message("Search Parameters sheet not found")
            return
        
        # Find the last row and add status
        values = worksheet.get_all_values()
        next_row = len(values) + 2
        
        # Update status
        worksheet.update(f'A{next_row}:C{next_row}', [['Pipeline Status', status, message]])
        worksheet.update(f'A{next_row + 1}:B{next_row + 1}', [['Last Updated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
        
        log_message(f"Status updated in Google Sheets: {status}")
        
    except Exception as e:
        log_message(f"Error updating sheet status: {e}")

def run_mvp_script():
    """Run the MVP script in a separate thread"""
    try:
        log_message("Starting MVP script execution...")
        update_sheet_status("RUNNING", f"Pipeline started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Change to script directory
        script_dir = os.path.dirname(SCRIPT_PATH)
        
        # Run the Python script
        result = subprocess.run(
            ['python', 'mvp.py'],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            log_message("MVP script completed successfully")
            update_sheet_status("COMPLETED", f"Pipeline completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log_message("Script output:")
            log_message(result.stdout)
        else:
            log_message(f"MVP script failed with return code: {result.returncode}")
            update_sheet_status("ERROR", f"Pipeline failed with error code {result.returncode}")
            log_message("Script error output:")
            log_message(result.stderr)
            
    except subprocess.TimeoutExpired:
        log_message("MVP script timed out after 1 hour")
        update_sheet_status("ERROR", "Pipeline timed out after 1 hour")
    except Exception as e:
        log_message(f"Error running MVP script: {e}")
        update_sheet_status("ERROR", f"Error running pipeline: {str(e)}")

@app.route('/run-mvp', methods=['POST'])
def trigger_mvp():
    """Webhook endpoint to trigger MVP script"""
    try:
        # Get request data
        data = request.get_json() or {}
        
        log_message(f"Received trigger request: {data}")
        
        # Validate request
        if data.get('action') != 'run_mvp':
            return jsonify({'error': 'Invalid action'}), 400
        
        # Check if script is already running
        if is_script_running():
            log_message("Script is already running, ignoring request")
            return jsonify({'error': 'Script is already running'}), 409
        
        # Start script in background thread
        thread = threading.Thread(target=run_mvp_script)
        thread.daemon = True
        thread.start()
        
        log_message("MVP script started in background")
        
        return jsonify({
            'status': 'success',
            'message': 'MVP pipeline started successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        log_message(f"Error in webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current status of the pipeline"""
    try:
        is_running = is_script_running()
        
        # Read last few log entries
        recent_logs = []
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                recent_logs = f.readlines()[-10:]  # Last 10 lines
        except:
            pass
        
        return jsonify({
            'is_running': is_running,
            'recent_logs': [log.strip() for log in recent_logs],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def is_script_running():
    """Check if the MVP script is currently running"""
    try:
        # Check for running Python processes with mvp.py
        result = subprocess.run(
            ['pgrep', '-f', 'mvp.py'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        # Fallback method for Windows
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe'],
                capture_output=True,
                text=True
            )
            return 'mvp.py' in result.stdout
        except:
            return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'script_path': SCRIPT_PATH,
        'script_exists': os.path.exists(SCRIPT_PATH)
    })

if __name__ == '__main__':
    log_message("Starting webhook server...")
    log_message(f"Script path: {SCRIPT_PATH}")
    log_message(f"Log file: {LOG_FILE}")
    
    # Check if script exists
    if not os.path.exists(SCRIPT_PATH):
        log_message(f"Warning: Script not found at {SCRIPT_PATH}")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)