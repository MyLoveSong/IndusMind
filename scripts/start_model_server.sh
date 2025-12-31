#!/bin/bash

# Start Local QWEN3-8B Model Server
# This script starts the Python server that serves the fine-tuned QWEN3-8B model

echo "🚀 Starting Local QWEN3-8B Model Server..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables
export MODEL_SERVER_HOST="${MODEL_SERVER_HOST:-127.0.0.1}"
export MODEL_SERVER_PORT="${MODEL_SERVER_PORT:-8001}"
export LOCAL_QWEN_API_KEY="${LOCAL_QWEN_API_KEY:-}"

echo "Starting model server on $MODEL_SERVER_HOST:$MODEL_SERVER_PORT"
echo "API Key: ${LOCAL_QWEN_API_KEY:+configured}"

# Start the server
python QWEN3-8B/model_server.py
