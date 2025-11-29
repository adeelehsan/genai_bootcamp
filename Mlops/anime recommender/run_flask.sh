#!/bin/bash

# Run Flask Anime Recommender Application

echo "🎌 Starting Anime Recommender Flask App..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python3 -m venv venv"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Make sure to create .env with GROQ_API_KEY"
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip install flask --quiet
fi

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

echo "🚀 Starting Flask server..."
echo "📍 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the Flask app
python app.py
