#!/bin/bash
# Startup script to ensure Chrome and ChromeDriver are installed before starting API

echo "=== MatchTrex Startup Script ==="
echo "Checking Chrome installation..."

if ! command -v google-chrome &> /dev/null; then
    echo "Chrome not found, installing..."
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq wget gnupg2 unzip > /dev/null 2>&1
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - > /dev/null 2>&1
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq google-chrome-stable > /dev/null 2>&1
    echo "✅ Chrome installed: $(google-chrome --version)"
else
    echo "✅ Chrome already installed: $(google-chrome --version)"
fi

echo "Checking ChromeDriver installation..."
if [ ! -f /usr/local/bin/chromedriver ]; then
    echo "ChromeDriver not found, installing..."
    CHROME_FULL_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
    echo "   Chrome version detected: $CHROME_FULL_VERSION"

    # Try to download ChromeDriver with error handling
    DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_FULL_VERSION}/linux64/chromedriver-linux64.zip"
    echo "   Downloading from: $DOWNLOAD_URL"

    if wget -q "$DOWNLOAD_URL" -O /tmp/chromedriver.zip; then
        if unzip -q /tmp/chromedriver.zip -d /tmp 2>/dev/null; then
            if [ -f /tmp/chromedriver-linux64/chromedriver ]; then
                mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
                chmod +x /usr/local/bin/chromedriver
                rm -rf /tmp/chromedriver*
                echo "✅ ChromeDriver installed: $(/usr/local/bin/chromedriver --version)"
            else
                echo "❌ ChromeDriver binary not found in download"
            fi
        else
            echo "❌ Failed to extract ChromeDriver zip"
            rm -f /tmp/chromedriver.zip
        fi
    else
        echo "❌ Failed to download ChromeDriver"
    fi
else
    echo "✅ ChromeDriver already installed: $(/usr/local/bin/chromedriver --version)"
fi

echo ""
echo "=== Starting MatchTrex API ==="
echo "Chrome setup complete! Starting API on port 3001..."
echo ""

# Start the API
# Try different virtual environment paths
if [ -f venv/bin/activate ]; then
    echo "Using local venv..."
    source venv/bin/activate && python api.py --port 3001
elif [ -f /app/venv/bin/activate ]; then
    echo "Using /app/venv..."
    source /app/venv/bin/activate && python api.py --port 3001
else
    echo "No venv found, using system Python..."
    python3 api.py --port 3001
fi