#!/bin/bash
# Setup script for GRT Bus Time on Raspberry Pi

echo "Setting up GRT Bus Time..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "To run the script:"
echo "  source venv/bin/activate"
echo "  nohup python bus_arrival_times.py"
