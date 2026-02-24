#!/bin/bash
# Launch Guitar Practice App in Kiosk Mode
# For Raspberry Pi with TV display

# Change to app directory
cd "$(dirname "$0")"

# Start Flask app in background
echo "Starting Guitar Practice App..."
./start.sh &
FLASK_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "Error: Server failed to start"
    exit 1
fi

echo "Server is ready!"
echo "Launching kiosk mode..."

# Launch Chromium in kiosk mode
# Adjust the browser command based on your system
if command -v chromium-browser &> /dev/null; then
    chromium-browser --kiosk --disable-infobars --noerrdialogs --disable-session-crashed-bubble http://localhost:5000
elif command -v chromium &> /dev/null; then
    chromium --kiosk --disable-infobars --noerrdialogs --disable-session-crashed-bubble http://localhost:5000
elif command -v google-chrome &> /dev/null; then
    google-chrome --kiosk --disable-infobars --noerrdialogs --disable-session-crashed-bubble http://localhost:5000
else
    echo "Error: No compatible browser found (chromium-browser, chromium, or google-chrome)"
    echo "Falling back to default browser..."
    xdg-open http://localhost:5000
fi

# When browser closes, stop Flask
echo "Kiosk mode closed. Stopping server..."
kill $FLASK_PID 2>/dev/null
