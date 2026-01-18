#!/bin/bash
# Launch Omarchy Theme Picker webapp

PROJECT_DIR="$HOME/1.projects/omarchythemes"
PORT_FILE="$PROJECT_DIR/.port"
DEFAULT_PORT=8420

# Function to get the current port
get_port() {
    if [[ -f "$PORT_FILE" ]]; then
        cat "$PORT_FILE"
    else
        echo "$DEFAULT_PORT"
    fi
}

# Function to check if server is running on a port
server_running() {
    curl -s --connect-timeout 1 "http://127.0.0.1:$1/api/themes" > /dev/null 2>&1
}

# Check if server is already running on the saved port
PORT=$(get_port)
if ! server_running "$PORT"; then
    # Remove old port file
    rm -f "$PORT_FILE"

    # Start the server (it will find a free port and write to .port)
    cd "$PROJECT_DIR"
    source .venv/bin/activate
    nohup python server.py > /tmp/omarchy-themes.log 2>&1 &

    # Wait for port file to be created and server to be ready
    for i in {1..20}; do
        sleep 0.3
        if [[ -f "$PORT_FILE" ]]; then
            PORT=$(cat "$PORT_FILE")
            server_running "$PORT" && break
        fi
    done
fi

# Launch as webapp
exec omarchy-launch-webapp "http://127.0.0.1:$PORT"
