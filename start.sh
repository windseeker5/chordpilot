#!/bin/bash
# Start script for Guitar Practice App

# Change to app directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start Flask app
export FLASK_APP=app.py
export FLASK_ENV=development

echo "Starting Guitar Practice App..."
echo "Access at: http://localhost:5000"
echo "Press Ctrl+C to stop"

# Run Flask
python -m flask run --host=0.0.0.0 --port=5000
