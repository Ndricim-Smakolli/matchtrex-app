#!/bin/bash

echo "Installing Chrome and ChromeDriver on Ubuntu/Debian VPS..."

# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install -y wget gnupg2 unzip curl

# Add Google Chrome's official repository
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update package list again
sudo apt-get update

# Install Google Chrome
sudo apt-get install -y google-chrome-stable

# Get Chrome version
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
echo "Installed Chrome version: $CHROME_VERSION"

# Install ChromeDriver using the new JSON API
# Get the major version number
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1)

echo "Looking for ChromeDriver for Chrome major version: $CHROME_MAJOR_VERSION"

# Use the new ChromeDriver download endpoint
CHROME_FULL_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
echo "Full Chrome version: $CHROME_FULL_VERSION"

# Get the ChromeDriver download URL from the new JSON API
CHROMEDRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json" | \
    grep -B 10 "\"$CHROME_MAJOR_VERSION\." | \
    grep -o '"https://[^"]*chromedriver-linux64.zip"' | \
    tail -1 | \
    tr -d '"')

if [ -z "$CHROMEDRIVER_URL" ]; then
    echo "Could not find ChromeDriver URL, trying alternative method..."
    # Fallback to direct URL construction
    CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"
fi

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"

# Download and install ChromeDriver
wget -q "$CHROMEDRIVER_URL" -O chromedriver-linux64.zip
unzip -o chromedriver-linux64.zip
if [ -d "chromedriver-linux64" ]; then
    sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
else
    sudo mv chromedriver /usr/local/bin/
fi
sudo chmod +x /usr/local/bin/chromedriver
rm -rf chromedriver-linux64.zip chromedriver-linux64

# Install additional dependencies for headless Chrome (only available packages)
sudo apt-get install -y \
    xvfb \
    libxi6 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils || true

echo ""
echo "====================================="
echo "Chrome and ChromeDriver installation complete!"
echo "Chrome version: $(google-chrome --version)"
echo "ChromeDriver version: $(/usr/local/bin/chromedriver --version 2>/dev/null || echo 'Not found at /usr/local/bin/chromedriver')"
echo ""
echo "Testing ChromeDriver..."
/usr/local/bin/chromedriver --version || echo "ChromeDriver test failed"
echo "====================================="