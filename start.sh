#!/bin/bash

# Ryzen Master Commander startup script
# This script can be used for system startup or manual execution

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
APP_DIR="$SCRIPT_DIR"
VENV_PATH="$APP_DIR/venv"
PYTHON_MODULE="src.main"
LOG_DIR="$HOME/.local/share/ryzen-master-commander/logs"
LOG_FILE="$LOG_DIR/startup.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Start the application
log "Starting Ryzen Master Commander..."

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    error_exit "Application directory not found: $APP_DIR"
fi

# Change to app directory
cd "$APP_DIR" || error_exit "Failed to change to directory: $APP_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    error_exit "Virtual environment not found: $VENV_PATH"
fi

# Activate virtual environment
log "Activating virtual environment..."
source "$VENV_PATH/bin/activate" || error_exit "Failed to activate virtual environment"

# Check if Python module exists
if [ ! -d "$APP_DIR/src" ]; then
    error_exit "Source directory not found: $APP_DIR/src"
fi

# Run the application
log "Launching application..."
python -m "$PYTHON_MODULE" 2>&1 | tee -a "$LOG_FILE"

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "Application exited normally"
else
    log "Application exited with code: $EXIT_CODE"
fi

exit $EXIT_CODE
