#!/bin/bash
set -e

echo "================================================"
echo "🚀 Starting RAG Medical Chatbot"
echo "================================================"

# Check if vectorstore exists
if [ -d "vectorstore/db_faiss" ]; then
    echo "✅ Vectorstore found at vectorstore/db_faiss"
    ls -lh vectorstore/db_faiss/
else
    echo "❌ ERROR: Vectorstore not found at vectorstore/db_faiss"
    echo "Contents of current directory:"
    ls -la
    exit 1
fi

# Check environment variables
if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  WARNING: GROQ_API_KEY not set"
else
    echo "✅ GROQ_API_KEY is set"
fi

echo "================================================"
echo "🔧 Starting Flask application on port 5000"
echo "================================================"

# Start the Flask app
exec python app/application.py
