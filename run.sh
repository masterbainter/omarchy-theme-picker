#!/bin/bash
cd "$(dirname "$0")"

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "Starting Omarchy Theme Picker at http://127.0.0.1:8420"
python server.py
