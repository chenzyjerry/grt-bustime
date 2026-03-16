#!/bin/bash
# Wrapper script to run GRT Bus Time on startup

# Set working directory to script location
cd "$(dirname "$0")" || exit 1

# Activate virtual environment
source venv/bin/activate

# Run the Python script and log output
python3 bus_arrival_times.py >> bustime.log 2>&1
