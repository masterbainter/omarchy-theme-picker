#!/bin/bash
# Launch Omarchy Theme Picker webapp

PROJECT_DIR="$HOME/1.projects/omarchythemes"
PORT=8420
URL="http://127.0.0.1:$PORT"

# Check if server is already running
if ! curl -s --connect-timeout 1 "$URL/api/themes" > /dev/null 2>&1; then
    # Start the server
    cd "$PROJECT_DIR"
    source .venv/bin/activate
    nohup python server.py > /tmp/omarchy-themes.log 2>&1 &

    # Wait for server to be ready
    for i in {1..10}; do
        sleep 0.3
        curl -s --connect-timeout 1 "$URL/api/themes" > /dev/null 2>&1 && break
    done
fi

# Launch as webapp
exec omarchy-launch-webapp "$URL"
