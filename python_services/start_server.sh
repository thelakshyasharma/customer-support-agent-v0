#!/bin/bash

# Make script exit on any error
set -e

# Display message
echo "Cleaning up any existing server processes..."

# Kill any existing uvicorn processes more aggressively
pkill -9 -f uvicorn 2>/dev/null || true
pkill -9 -f "python.*uvicorn" 2>/dev/null || true

# Wait for processes to terminate
sleep 3

# Set port (default 8000)
PORT=${1:-8000}

# Check if the port is in use, and if so, incrementally try other ports
check_port() {
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:"$1" >/dev/null 2>&1; then
            return 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tuln | grep -q ":$1 "; then
            return 1
        fi
    fi
    return 0
}

# Find available port
while ! check_port "$PORT"; do
    echo "Port $PORT is already in use, trying next port..."
    PORT=$((PORT + 1))
done

# Display message
echo "Starting server on http://127.0.0.1:$PORT"

# Change to python_services directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate || source ./venv/bin/activate

# Start the FastAPI application
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port $PORT 