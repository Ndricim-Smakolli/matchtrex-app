#!/bin/bash
# Startup script to ensure Chrome and ChromeDriver are installed

echo "Checking Chrome installation..."
if ! command -v google-chrome &> /dev/null; then
    echo "Chrome not found, installing..."
    apt-get update -qq
    apt-get install -y -qq wget gnupg2 unzip
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update -qq
    apt-get install -y -qq google-chrome-stable
    echo "Chrome installed: $(google-chrome --version)"
fi

echo "Checking ChromeDriver installation..."
if [ ! -f /usr/local/bin/chromedriver ]; then
    echo "ChromeDriver not found, installing..."
    CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip
    unzip -q /tmp/chromedriver.zip -d /tmp
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
    chmod +x /usr/local/bin/chromedriver
    rm -rf /tmp/chromedriver*
    echo "ChromeDriver installed: $(/usr/local/bin/chromedriver --version)"
fi

# Start the API
echo "Starting API..."
source venv/bin/activate && python api.py --port 3001